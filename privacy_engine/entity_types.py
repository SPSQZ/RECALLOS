# privacy_engine/entity_types.py
import re
from enum import Enum
from typing import Dict, Pattern


class EntityType(str, Enum):
    """Supported PII entity categories for RecallOS local redaction."""
    NAME = "NAME"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    FINANCIAL_ORG = "FINANCIAL_ORG"
    AMOUNT = "AMOUNT"
    CREDENTIAL = "CREDENTIAL"

    def format_token(self, index: int) -> str:
        """Generates deterministic placeholder token, e.g., [REDACTED_NAME_1]."""
        return f"[REDACTED_{self.value}_{index}]"


# Pre-compiled Regex patterns for fast, zero-latency deterministic detection
REGEX_PATTERNS: Dict[EntityType, Pattern] = {
    # Matches API keys, secret tokens, and 9-to-16 digit routing/account numbers
    EntityType.CREDENTIAL: re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|\d{9,16})\b"
    ),

    # Matches standard emails (e.g., user.name@domain.com)
    EntityType.EMAIL: re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b"
    ),
    
    # Matches international & local phone formats (e.g., +91 9876543210, +1-555-019-2834, (555) 123-4567)
    EntityType.PHONE: re.compile(
        r"(?:\+\d{1,3}[\s-]?)?\(?\d{3,5}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"
    ),
    
    # Matches currency values & amounts (e.g., $5,000, ₹10,000.50, USD 250, 10000 INR)
    EntityType.AMOUNT: re.compile(
        r"(?:[\$₹€£]\s?\d+(?:,\d{3})*(?:\.\d{1,2})?\b|\b\d+(?:,\d{3})*(?:\.\d{1,2})?\s?(?:USD|INR|EUR|dollars|rupees)\b)",
        re.IGNORECASE,
    ),
    
    # Matches common banks, payment networks, & financial institutions
    EntityType.FINANCIAL_ORG: re.compile(
        r"\b(?:Chase|Citibank|Wells\s+Fargo|Bank\s+of\s+America|Goldman\s+Sachs|Morgan\s+Stanley|"
        r"HDFC(?:\s+Bank)?|ICICI(?:\s+Bank)?|SBI|State\s+Bank\s+of\s+India|Axis\s+Bank|Kotak|"
        r"PayPal|Stripe|Visa|Mastercard|Amex|American\s+Express|Fidelity|Vanguard)\b",
        re.IGNORECASE,
    ),
}

# Matches any generated token during rehydration (e.g., [REDACTED_EMAIL_1])
REDACTED_TOKEN_PATTERN: Pattern = re.compile(
    r"\[REDACTED_(?:NAME|PHONE|EMAIL|FINANCIAL_ORG|AMOUNT|CREDENTIAL)_\d+\]",
    re.IGNORECASE,
)
