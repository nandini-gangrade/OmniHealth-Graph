import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.agents.llm import get_llm, response_text, strip_fences
from app.services.falkor_service import falkor_service

logger = logging.getLogger(__name__)

CLINICAL_PROMPT = """
You are an expert Clinical Documentation Agent. Your job is to analyze the patient-doctor conversation and the retrieved medical guidelines, and generate structured clinical documents.

Input Conversation:
{transcript}

Graph-retrieved context (FalkorDB: symptoms, patient memory):
{guidelines}

Generate the following in valid JSON format matching this schema:
{{
    "soap_notes": {{
        "subjective": "detailed subjective patient complaints, history of present illness (HPI), compliance",
        "objective": "physical exam notes, vital signs, lung sounds, observations from transcript",
        "assessment": "diagnoses with ICD-10 suggestions, rationale",
        "plan": "medications, testing ordered, follow-ups, advice"
    }},
    "progress_notes": "clinical progress summary line",
    "visit_summary": "patient-friendly visit summary",
    "discharge_summary": "discharge guidelines and instructions",
    "medication_summary": [
        {{"name": "medication name", "dosage": "dose", "frequency": "frequency", "duration": "duration"}}
    ],
    "treatment_plan": "overall care instructions summary",
    "fhir_output": {{
        "resource_type": "Bundle",
        "fhir_json": {{
             "resourceType": "Bundle",
             "type": "collection",
             "entry": [
                 // list of FHIR resources representing patient conditions, observations, or medication orders
             ]
        }}
    }}
}}

Make sure to output ONLY the raw JSON document, no markdown codeblock wrapper, no comments, just valid JSON.
"""

class ClinicalAgent:
    def __init__(self):
        self.llm = get_llm()

    async def generate_documentation(
        self, transcript: str, guidelines: str, patient_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Returns (clinical_notes, contraindication_alerts).

        After the SOAP note is drafted, every newly prescribed medication is checked against the
        patient's *historical* active medications stored in their isolated FalkorDB subgraph.
        """
        logger.info("Generating clinical documentation...")
        prompt = CLINICAL_PROMPT.format(transcript=transcript, guidelines=guidelines)
        try:
            data = json.loads(strip_fences(response_text(self.llm.invoke(prompt))))
        except Exception as e:
            logger.error(f"Error in ClinicalAgent: {e}. Utilizing fallback generation.")
            from app.agents.llm import SimulatedLLM
            data = json.loads(SimulatedLLM().invoke(prompt.replace("Retrieved", "")).content)

        alerts: List[Dict[str, Any]] = []
        if patient_id:
            seen = set()
            for med in data.get("medication_summary", []) or []:
                name = " ".join(str(x) for x in (med.get("name"), med.get("dosage")) if x)
                if not med.get("name"):
                    continue
                for hit in falkor_service.check_cross_session_contraindications(patient_id, name):
                    key = (hit["new_medication"], hit["conflicting_medication"])
                    if key not in seen:
                        seen.add(key)
                        alerts.append(hit)
        if alerts:
            banner = "\n".join(
                f"!! CONTRAINDICATION ALERT [{a['severity']}]: {a['message']} "
                f"Graph path: {' -> '.join(a['trace_path'])}. Do NOT co-prescribe without physician review."
                for a in alerts
            )
            soap = data.setdefault("soap_notes", {})
            soap["plan"] = f"{banner}\n\n{soap.get('plan', '')}".strip()
        return data, alerts


# Global instance
clinical_agent = ClinicalAgent()
