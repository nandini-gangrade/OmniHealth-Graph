import json
import logging
from typing import List, Dict, Any
from app.agents.llm import get_llm, response_text, strip_fences
from app.services.falkor_service import falkor_service

logger = logging.getLogger(__name__)

CODING_PROMPT = """
You are a certified Medical Coding Agent. Analyze the patient transcript and clinical SOAP notes, and recommend billing codes.

Transcript:
{transcript}

Clinical SOAP Notes:
{soap_notes}

Graph-retrieved context (FalkorDB):
{guidelines}

Recommend all matching codes:
1. ICD-10 Diagnosis Codes
2. CPT Procedure Codes
3. HCPCS Codes (if applicable)

Return a list of JSON objects matching this format:
[
    {{
        "code": "ICD-10 or CPT code",
        "system": "ICD-10" or "CPT" or "HCPCS",
        "description": "official description",
        "confidence": 0.0 to 1.0,
        "supporting_evidence": "exact text quotes or justification from transcript/notes supporting this code",
        "reimbursement_estimate": 0.00
    }}
]

Output ONLY the raw JSON list, without any markdown codeblock format.
"""


class CodingAgent:
    def __init__(self):
        self.llm = get_llm()

    async def recommend_codes(self, transcript: str, soap_notes: Dict[str, Any], guidelines: str) -> List[Dict[str, Any]]:
        """LLM proposes codes; FalkorDB proves (or fails to prove) medical necessity for each CPT."""
        logger.info("Extracting ICD-10 and CPT coding recommendations...")
        prompt = CODING_PROMPT.format(transcript=transcript, soap_notes=json.dumps(soap_notes), guidelines=guidelines)
        try:
            codes = json.loads(strip_fences(response_text(self.llm.invoke(prompt))))
        except Exception as e:
            logger.error(f"Error in CodingAgent: {e}. Utilizing fallback coding recommendations.")
            from app.agents.llm import SimulatedLLM
            codes = json.loads(SimulatedLLM().invoke(prompt.replace("Graph-retrieved", "")).content)
        return codes

    def attach_necessity(self, codes: List[Dict[str, Any]], transcript: str, soap_notes: Dict[str, Any]):
        """Replaces vector RAG: multi-hop Symptom->Diagnosis->Procedure Cypher for every CPT code.

        Returns (codes_with_trace, necessity_records, symptoms).
        """
        text = f"{transcript}\n{soap_notes.get('subjective', '')}\n{soap_notes.get('assessment', '')}"
        symptoms = falkor_service.extract_symptoms(text)
        icd = [c["code"] for c in codes if c.get("system") == "ICD-10"]
        records = []
        for c in codes:
            if c.get("system") != "CPT":
                continue
            res = falkor_service.verify_medical_necessity(symptoms, c["code"]) if symptoms else \
                {"verified": False, "trace_path": []}
            if not res.get("verified"):
                res = falkor_service.verify_necessity_from_diagnoses(icd, c["code"])
            c["necessity_verified"] = bool(res.get("verified"))
            c["trace_path"] = res.get("trace_path", [])
            records.append({"cpt": c["code"], "verified": c["necessity_verified"], "trace_path": c["trace_path"],
                            "icd": res.get("icd"), "basis": res.get("basis", "symptom"), "engine": res.get("engine", "falkordb"),
                            "error": res.get("error")})
        return codes, records, symptoms


# Global instance
coding_agent = CodingAgent()
