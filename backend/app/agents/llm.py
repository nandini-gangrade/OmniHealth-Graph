import logging
import json
from typing import Any
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    has_gemini = True
except ImportError:  # pragma: no cover
    has_gemini = False


def response_text(response: Any) -> str:
    """Gemini via LangChain may return content as a list of parts; normalise to a plain string."""
    content = getattr(response, "content", response)
    if isinstance(content, list):
        content = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return str(content).strip()


def strip_fences(content: str) -> str:
    import re
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    return content


def get_llm():
    """Gemini (temperature 0.1 for deterministic clinical reasoning) or the offline simulator."""
    if has_gemini and settings.GEMINI_API_KEY:
        try:
            logger.info("Initializing Gemini chat model: %s", settings.GEMINI_MODEL)
            return ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                temperature=0.1,
                google_api_key=settings.GEMINI_API_KEY,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini ({e}). Using simulated Clinical Engine.")
    else:
        logger.info("GEMINI_API_KEY not set (or langchain-google-genai missing). Using simulated Clinical LLM Engine.")
    return SimulatedLLM()


class SimulatedLLM:
    """Mock LLM response generator that matches system prompts and returns realistic clinical text."""
    
    def invoke(self, messages: Any) -> Any:
        # Convert messages to string to extract prompts
        prompt_text = ""
        if isinstance(messages, str):
            prompt_text = messages
        elif isinstance(messages, list):
            prompt_text = "\n".join([getattr(m, "content", str(m)) for m in messages])
        else:
            prompt_text = str(messages)

        # Output mock class
        class MockAIMessage:
            def __init__(self, content):
                self.content = content
                self.response_metadata = {
                    "token_usage": {"prompt_tokens": 1200, "completion_tokens": 800, "total_tokens": 2000},
                    "model_name": "simulated-clinical-engine",
                    "system_fingerprint": "fp_mock_123"
                }

        # Route prompts to mock generators
        content = self._generate_response(prompt_text)
        return MockAIMessage(content)

    def _generate_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        
        # 1. Clinical Documentation Agent
        cardiac = "nitroglycerin" in prompt_lower or "angina" in prompt_lower
        if "clinical documentation agent" in prompt_lower or prompt_lower.strip() == "soap subjective":
            if cardiac:
                return json.dumps(CARDIAC_SOAP)
            return json.dumps({
                "soap_notes": {
                    "subjective": "Patient presents with a 3-week history of worsening dry cough, mild wheezing, and exertional chest tightness. Denies fever, chills, or colored sputum. Reports mild pain in the right knee during normal ambulation, which has been chronic for 6 months. History of high blood pressure, compliant with Amlodipine.",
                    "objective": "BP: 138/84 mmHg, HR: 72 bpm, Temp: 98.2 F, RR: 16 bpm. Lungs: Mild expiratory wheezing bilaterally, no rales or rhonchi. Heart: Regular rate and rhythm, no murmurs. Right Knee: Mild patellar crepitus, no effusion or erythema. Range of motion intact but slightly painful on end-flexion.",
                    "assessment": "1. Acute Bronchitis (J20.9) - acute onset of cough and wheezing.\n2. Essential Hypertension (I10) - stable, slightly elevated readings.\n3. Unilateral Osteoarthritis, Right Knee (M17.11) - mild chronic joint friction.",
                    "plan": "1. Prescribed Albuterol HFA inhaler, 2 puffs every 4-6 hours as needed for wheezing.\n2. Advised increase in fluid intake and use of a humidifier.\n3. Ordered a standard 12-lead EKG to evaluate chest tightness.\n4. Recommended daily range-of-motion exercises for the right knee, OTC ibuprofen 400mg tid prn.\n5. Follow up in 2 weeks if symptoms do not improve."
                },
                "progress_notes": "Established patient returns with acute cough. Examination reveals bilateral wheezing. Stable hypertension on current medication. Chronic right knee pain addressed.",
                "visit_summary": "The patient was evaluated for a persistent dry cough and chest tightness. Clear signs of mild bronchial inflammation were detected. Prescribed a rescue inhaler and ordered an EKG to rule out cardiac issues. The patient's knee osteoarthritis and blood pressure management were also reviewed.",
                "discharge_summary": "Patient stable for discharge. Resume normal activities. Use Albuterol inhaler as directed. Complete EKG before leaving the clinic. Follow up in 14 days.",
                "medication_summary": [
                    {"name": "Albuterol HFA Inhaler", "dosage": "90 mcg/actuation", "frequency": "1-2 puffs q4-6h prn", "duration": "14 days"},
                    {"name": "Amlodipine", "dosage": "5 mg", "frequency": "Once daily", "duration": "Chronic"}
                ],
                "treatment_plan": "Albuterol therapy, EKG execution, conservative osteoarthritis management, and blood pressure monitoring.",
                "fhir_output": {
                    "resource_type": "Bundle",
                    "fhir_json": {
                        "resourceType": "Bundle",
                        "type": "collection",
                        "entry": [
                            {"resource": {"resourceType": "Encounter", "status": "finished", "class": {"code": "AMB"}}},
                            {"resource": {"resourceType": "Condition", "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "J20.9"}]}}},
                            {"resource": {"resourceType": "Condition", "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10"}]}}},
                            {"resource": {"resourceType": "Procedure", "status": "completed", "code": {"coding": [{"system": "http://www.ama-assn.org/go/cpt", "code": "93000"}]}}}
                        ]
                    }
                }
            })

        # 2. Medical Coding Agent
        elif "medical coding agent" in prompt_lower or "cpt coding recommendations" in prompt_lower:
            if cardiac:
                return json.dumps(CARDIAC_CODES)
            return json.dumps([
                {
                    "code": "J20.9",
                    "system": "ICD-10",
                    "description": "Acute bronchitis, unspecified",
                    "confidence": 0.95,
                    "supporting_evidence": "Patient presents with persistent cough, wheezing, and expiratory wheezing on chest auscultation.",
                    "reimbursement_estimate": 110.00
                },
                {
                    "code": "I10",
                    "system": "ICD-10",
                    "description": "Essential (primary) hypertension",
                    "confidence": 0.92,
                    "supporting_evidence": "History of high blood pressure and current blood pressure reading of 138/84 mmHg.",
                    "reimbursement_estimate": 150.00
                },
                {
                    "code": "M17.11",
                    "system": "ICD-10",
                    "description": "Unilateral primary osteoarthritis, right knee",
                    "confidence": 0.88,
                    "supporting_evidence": "Patient reports chronic right knee pain during normal walking and physical crepitus during examination.",
                    "reimbursement_estimate": 220.00
                },
                {
                    "code": "99213",
                    "system": "CPT",
                    "description": "Office visit for the evaluation and management of an established patient (Low-to-Moderate Complexity, 15-29 minutes)",
                    "confidence": 0.90,
                    "supporting_evidence": "Routine checkup involving active management of two chronic conditions (Hypertension, Osteoarthritis) and one acute condition (Bronchitis).",
                    "reimbursement_estimate": 92.50
                },
                {
                    "code": "93000",
                    "system": "CPT",
                    "description": "Electrocardiogram, routine ECG with at least 12 leads; with interpretation and report",
                    "confidence": 0.98,
                    "supporting_evidence": "Ordered and performed during session to evaluate patient's complaints of exertional chest tightness.",
                    "reimbursement_estimate": 48.00
                }
            ])

        # 3. Compliance Agent
        elif "compliance and audit agent" in prompt_lower or "compliance score" in prompt_lower:
            return json.dumps({
                "missing_documentation": ["Detailed smoking history", "Spirometry testing considerations for chronic cough"],
                "medical_necessity_checked": True,
                "coding_completeness_score": 92.0,
                "cms_compliance_status": "Compliant with minor gaps",
                "documentation_gaps": ["No specific duration and pack-year details documented for patient's history of smoking or environmental exposures."]
            })

        # 4. Revenue Optimization Agent
        elif "revenue cycle optimization agent" in prompt_lower or "revenue leakage" == prompt_lower.strip():
            if cardiac:
                return json.dumps(CARDIAC_REVENUE)
            return json.dumps({
                "revenue_leakage_identified": [
                    "Missed billing for preventive medicine counseling (CPT 99401) regarding hypertension diet restrictions.",
                    "Potential upgrade of E&M code from CPT 99213 to CPT 99214 based on total consultation time and multiple managed conditions."
                ],
                "rejected_claim_probability": 8.5,
                "missing_billable_procedures": [
                    "CPT 99401: Preventive counseling (~15 mins)",
                    "CPT 36415: Venipuncture blood collection (if lab order was executed at clinic)"
                ],
                "revenue_score": 84.0,
                "estimated_reimbursement": 620.50
            })

        # 5. Reviewer Agent
        elif "reviewer agent" in prompt_lower or "reviewer hallucination" in prompt_lower:
            return json.dumps({
                "aggregate_confidence": 91.5,
                "hallucination_detected": False,
                "hallucination_details": "",
                "validated_citations": [
                    {"code": "J20.9", "source": "ICD-10 Guidelines Section 3"},
                    {"code": "99213", "source": "CPT E&M Selection Manual 2026"}
                ],
                "reviewer_notes": "All generated clinical terms align perfectly with raw transcript. Citations validated successfully against the loaded guidelines collection."
            })

        # Default fallback
        return "Simulated clinical model execution successful."


# --- Offline simulator fixtures for the angina / nitroglycerin demo (Robert Vance) ---
CARDIAC_SOAP = {
    "soap_notes": {
        "subjective": "58-year-old male with type 2 diabetes and hypertension reports 2 weeks of exertional chest tightness on climbing stairs, relieved by rest within 5 minutes. No radiation, diaphoresis or syncope.",
        "objective": "BP 146/90 mmHg, HR 78 bpm, SpO2 98%. Heart: regular rate and rhythm, no murmurs. Lungs clear. 12-lead ECG ordered. Point-of-care glucose pending.",
        "assessment": "1. Angina pectoris, unspecified (I20.9) - exertional pattern.\n2. Type 2 diabetes mellitus without complications (E11.9).\n3. Essential hypertension (I10).",
        "plan": "1. Prescribe Nitroglycerin 0.4 mg sublingual PRN chest pain.\n2. 12-lead ECG today (CPT 93000).\n3. Quantitative blood glucose (CPT 82947).\n4. Continue Metformin 500 mg BID.\n5. Cardiology follow-up in 1 week; return precautions for rest pain."
    },
    "progress_notes": "Established patient with new exertional chest tightness; ECG and glucose ordered; nitroglycerin PRN started.",
    "visit_summary": "You were seen for chest tightness that comes on with exertion. We are checking an ECG and blood sugar today and starting a rescue medicine for chest pain.",
    "discharge_summary": "Stable for discharge. Use nitroglycerin as directed. Call emergency services for pain that does not resolve with rest.",
    "medication_summary": [
        {"name": "Nitroglycerin", "dosage": "0.4 mg sublingual", "frequency": "PRN chest pain", "duration": "Ongoing"},
        {"name": "Metformin", "dosage": "500 mg", "frequency": "BID", "duration": "Chronic"}
    ],
    "treatment_plan": "Nitrate rescue therapy, ECG, glucose assay, cardiology follow-up.",
    "fhir_output": {"resource_type": "Bundle", "fhir_json": {"resourceType": "Bundle", "type": "collection", "entry": [
        {"resource": {"resourceType": "Condition", "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "I20.9"}]}}},
        {"resource": {"resourceType": "MedicationRequest", "status": "active", "medicationCodeableConcept": {"text": "Nitroglycerin 0.4 mg SL PRN"}}}
    ]}}
}

CARDIAC_CODES = [
    {"code": "I20.9", "system": "ICD-10", "description": "Angina pectoris, unspecified", "confidence": 0.94,
     "supporting_evidence": "exertional chest tightness relieved by rest", "reimbursement_estimate": 0.0},
    {"code": "E11.9", "system": "ICD-10", "description": "Type 2 diabetes mellitus without complications", "confidence": 0.91,
     "supporting_evidence": "history of type 2 diabetes, continuing Metformin", "reimbursement_estimate": 0.0},
    {"code": "I10", "system": "ICD-10", "description": "Essential (primary) hypertension", "confidence": 0.9,
     "supporting_evidence": "BP 146/90 mmHg with known hypertension", "reimbursement_estimate": 0.0},
    {"code": "99214", "system": "CPT", "description": "Office visit, established patient, moderate complexity", "confidence": 0.9,
     "supporting_evidence": "multiple chronic conditions plus new problem with prescription drug management", "reimbursement_estimate": 130.0},
    {"code": "93000", "system": "CPT", "description": "Electrocardiogram, routine ECG with at least 12 leads; with interpretation and report", "confidence": 0.97,
     "supporting_evidence": "12-lead ECG ordered for chest tightness", "reimbursement_estimate": 17.0},
    {"code": "93010", "system": "CPT", "description": "Electrocardiogram, interpretation and report only", "confidence": 0.55,
     "supporting_evidence": "physician interpretation of ECG (LLM suggestion - overlaps 93000)", "reimbursement_estimate": 9.0},
    {"code": "82947", "system": "CPT", "description": "Glucose; quantitative, blood", "confidence": 0.88,
     "supporting_evidence": "quantitative blood glucose ordered", "reimbursement_estimate": 5.0}
]

CARDIAC_REVENUE = {
    "revenue_leakage_identified": [
        "Venipuncture (CPT 36415) not captured if the glucose specimen is drawn in clinic.",
        "Confirm documentation supports moderate MDM so 99214 is not down-coded to 99213."
    ],
    "rejected_claim_probability": 11.0,
    "missing_billable_procedures": ["CPT 36415: Venipuncture, routine blood collection"],
    "revenue_score": 86.0,
    "estimated_reimbursement": 161.0
}
