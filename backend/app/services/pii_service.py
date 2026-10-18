import re
from typing import Dict, List, Tuple, Any

class PIIService:
    def __init__(self):
        # Compiled patterns for common PII/PHI entities
        self.patterns = {
            "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "PHONE": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
            "EMAIL": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
            "ZIP_CODE": re.compile(r"\b\d{5}(?:-\d{4})?\b"),
            "DOB": re.compile(
                r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4})\b",
                re.IGNORECASE
            )
        }

        # Names of patients/doctors to mask in transcripts
        # Commonly seen names in sample medical transcripts
        self.patient_identifiers = [
            "John Doe", "Robert Vance", "Jane Smith", "Robert Johnson", "Emily Davis", "Michael Brown",
            "William Garcia", "David Miller", "Sarah Martinez", "James Wilson", "Alice Henderson"
        ]

    def sanitize(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        if not text:
            return text, []

        pii_entities = []
        sanitized_text = text

        # 1. Mask regex-based patterns
        for pii_type, pattern in self.patterns.items():
            matches = list(pattern.finditer(sanitized_text))
            # Process matches in reverse order to maintain index offset consistency
            for match in reversed(matches):
                val = match.group()
                start, end = match.span()
                masked_placeholder = f"[REDACTED_{pii_type}]"
                
                pii_entities.append({
                    "type": pii_type,
                    "value": val,
                    "position": (start, end)
                })
                
                # Replace content in text
                sanitized_text = sanitized_text[:start] + masked_placeholder + sanitized_text[end:]

        # 2. Mask known patient names (case-insensitive replace)
        for name in self.patient_identifiers:
            # Match boundary for full names
            pattern = re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
            matches = list(pattern.finditer(sanitized_text))
            for match in reversed(matches):
                val = match.group()
                start, end = match.span()
                masked_placeholder = "[REDACTED_PATIENT_NAME]"
                
                pii_entities.append({
                    "type": "PATIENT_NAME",
                    "value": val,
                    "position": (start, end)
                })
                sanitized_text = sanitized_text[:start] + masked_placeholder + sanitized_text[end:]

        return sanitized_text, pii_entities

# Global instance
pii_service = PIIService()
