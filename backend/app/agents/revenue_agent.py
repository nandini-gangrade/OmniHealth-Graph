import json
import logging
import re
from typing import Dict, List, Any
from app.agents.llm import get_llm, response_text, strip_fences

logger = logging.getLogger(__name__)

REVENUE_PROMPT = """
You are a Healthcare Revenue Cycle Optimization Agent. Analyze the documentation and codes to find revenue opportunities.

SOAP Notes:
{soap_notes}

Current Recommended Codes:
{codes}

Tasks:
1. Identify any revenue leakage (e.g. procedures performed/mentioned in the transcript but not coded, or opportunities to counsel/vaccinate).
2. Calculate probability of claim rejection based on coding completeness and medical necessity (0% to 100%).
3. Identify missing billable procedures (e.g., CPT 99401 for health counseling, CPT 36415 for venipuncture).
4. Compute a Revenue Score (0-100; 100 means no leakage, lower means opportunities exist).
5. Estimate total reimbursement based on codes.

Return a JSON object:
{{
    "revenue_leakage_identified": ["leakage item 1", "leakage item 2"],
    "rejected_claim_probability": 0.0 to 100.0,
    "missing_billable_procedures": ["CPT XXXXX: description"],
    "revenue_score": 0.0 to 100.0,
    "estimated_reimbursement": 0.00
}}

Output ONLY raw JSON.
"""

class RevenueAgent:
    def __init__(self):
        self.llm = get_llm()

    async def optimize_revenue(self, soap_notes: Dict[str, Any], codes: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info("Analyzing revenue cycle and leakages...")
        soap_str = json.dumps(soap_notes)
        codes_str = json.dumps(codes)
        prompt = REVENUE_PROMPT.format(soap_notes=soap_str, codes=codes_str)
        
        try:
            response = self.llm.invoke(prompt)
            content = response_text(response)
            
            content = strip_fences(content)
            data = json.loads(content)
            return data
        except Exception as e:
            logger.error(f"Error in RevenueAgent: {e}. Utilizing fallback revenue report.")
            from app.agents.llm import SimulatedLLM
            response = SimulatedLLM().invoke("revenue leakage")
            return json.loads(response.content)

# Global instance
revenue_agent = RevenueAgent()
