import json
import logging
import re
from typing import Dict, Any, List
from app.agents.llm import get_llm, response_text, strip_fences
from app.services.falkor_service import falkor_service

logger = logging.getLogger(__name__)

COMPLIANCE_PROMPT = """
You are a CMS Compliance and Audit Agent. Review the clinical documentation and coding recommendations for gaps.

SOAP Notes:
{soap_notes}

Recommended Codes:
{codes}

Check:
1. Are there any clinical gaps (e.g. vital signs missing, duration of symptoms missing)?
2. Are the recommended codes supported by the clinical notes (Medical Necessity)?
3. Are there any coding completeness issues?

Return a JSON object:
{{
    "missing_documentation": ["item 1", "item 2"],
    "medical_necessity_checked": true or false,
    "coding_completeness_score": 0.0 to 100.0,
    "cms_compliance_status": "Compliant" or "Non-Compliant" or "Gaps Identified",
    "documentation_gaps": ["description of gaps in documentation"]
}}

Output ONLY raw JSON.
"""

class ComplianceAgent:
    def __init__(self):
        self.llm = get_llm()

    async def audit_compliance(
        self, soap_notes: Dict[str, Any], codes: List[Dict[str, Any]],
        necessity: List[Dict[str, Any]] | None = None, department: str | None = None,
    ) -> Dict[str, Any]:
        """LLM audit + graph-proven checks: necessity (from coding step), unbundling, institutional denial history."""
        logger.info("Auditing clinical and billing compliance...")
        prompt = COMPLIANCE_PROMPT.format(soap_notes=json.dumps(soap_notes), codes=json.dumps(codes))
        try:
            report = json.loads(strip_fences(response_text(self.llm.invoke(prompt))))
        except Exception as e:
            logger.error(f"Error in ComplianceAgent: {e}. Utilizing fallback audit.")
            from app.agents.llm import SimulatedLLM
            report = json.loads(SimulatedLLM().invoke("compliance score").content)

        necessity = necessity or []
        cpts = [c["code"] for c in codes if c.get("system") == "CPT"]
        unbundling = falkor_service.check_unbundling(cpts)
        dept = department or falkor_service.infer_department(cpts)
        dept_rows = falkor_service.get_department_compliance(dept) if dept else []

        gaps = list(report.get("documentation_gaps", []))
        for rec in necessity:
            if not rec["verified"]:
                gaps.append(f"CPT {rec['cpt']}: no Symptom/Diagnosis -> Procedure necessity path found in the knowledge graph (denial risk CO-50).")
        for u in unbundling:
            gaps.append(u["message"])
        report["documentation_gaps"] = gaps
        report["medical_necessity_checked"] = bool(necessity) and all(r["verified"] for r in necessity)
        if gaps and report.get("cms_compliance_status") == "Compliant":
            report["cms_compliance_status"] = "Gaps Identified"
        if unbundling:
            report["coding_completeness_score"] = min(float(report.get("coding_completeness_score", 100)), 80.0)
        # attached for the orchestrator (not part of ComplianceReport schema)
        report["_graph"] = {"unbundling": unbundling, "department": dept, "department_compliance": dept_rows}
        return report


# Global instance
compliance_agent = ComplianceAgent()
