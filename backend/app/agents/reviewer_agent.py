import json
import logging
import re
from typing import Dict, List, Any
from app.agents.llm import get_llm, response_text, strip_fences

logger = logging.getLogger(__name__)

REVIEWER_PROMPT = """
You are a Lead Clinical Reviewer Agent. Your task is to perform a final review of the generated clinical documentation, coding, compliance, and revenue optimization reports.

Clinical Documentation:
{clinical}

Codes:
{codes}

Compliance Report:
{compliance}

Revenue Report:
{revenue}

Tasks:
1. Double-check all information against the clinical documentation. Detect any hallucinations (unsupported assertions).
2. Validate citations of the guidelines used in the codes.
3. Calculate an aggregate clinical confidence score (0% to 100%).

Return a JSON object:
{{
    "aggregate_confidence": 0.0 to 100.0,
    "hallucination_detected": true or false,
    "hallucination_details": "details if detected, empty otherwise",
    "validated_citations": [
        {{"code": "code", "source": "validated source guideline detail"}}
    ],
    "reviewer_notes": "final audit remarks"
}}

Output ONLY raw JSON.
"""

class ReviewerAgent:
    def __init__(self):
        self.llm = get_llm()

    async def review_outputs(
        self, 
        clinical_notes: Dict[str, Any], 
        codes: List[Dict[str, Any]], 
        compliance: Dict[str, Any], 
        revenue: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info("Performing final review audit...")
        prompt = REVIEWER_PROMPT.format(
            clinical=json.dumps(clinical_notes),
            codes=json.dumps(codes),
            compliance=json.dumps(compliance),
            revenue=json.dumps(revenue)
        )
        
        try:
            response = self.llm.invoke(prompt)
            content = response_text(response)
            
            content = strip_fences(content)
            data = json.loads(content)
            return data
        except Exception as e:
            logger.error(f"Error in ReviewerAgent: {e}. Utilizing fallback reviewer audit.")
            from app.agents.llm import SimulatedLLM
            response = SimulatedLLM().invoke("reviewer hallucination")
            return json.loads(response.content)

# Global instance
reviewer_agent = ReviewerAgent()
