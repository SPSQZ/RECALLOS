# privacy_engine/scrubber.py
import re
from typing import Dict, List, Any, Optional
from privacy_engine.entity_types import EntityType, REGEX_PATTERNS

# Optional spaCy load with zero-crash fallback
try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except Exception:
    _NLP = None


class PIIScrubber:
    """
    Deterministic Local-First PII Tokenizer (Regex + Local NER).
    Replaces sensitive entities with [REDACTED_<TYPE>_<INDEX>] tokens.
    """

    def __init__(self) -> None:
        # Maps raw sensitive text -> [REDACTED_TYPE_N]
        self.entity_to_token: Dict[str, str] = {}
        # Maps [REDACTED_TYPE_N] -> raw sensitive text (used by Rehydrator)
        self.token_to_entity: Dict[str, str] = {}
        # Tracks sequential index per EntityType
        self.counters: Dict[EntityType, int] = {etype: 0 for etype in EntityType}

        # Contextual triggers (case-insensitive prefix, strict Title-Case name capture)
        self._name_triggers = re.compile(
            r"(?i:\b(?:my name is|i am|i'm|hey|hi|hello|dear|call|contact|pay|send to|transfer to|account to|to|from|mr\.?|ms\.?|mrs\.?|dr\.?|with))\s+"
            r"([A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20})?)\b"
        )
        # Common capitalized words to ignore in fallback NER
        self._stopwords = {
            "I", "The", "A", "An", "In", "On", "At", "To", "For", "Of", "With",
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
            "January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December",
            "RecallOS", "Nebius", "NVIDIA", "Nemotron", "Python", "Rust", "My", "Send", "Hey"
        }

    def _get_or_create_token(self, raw_value: str, entity_type: EntityType) -> str:
        """Returns existing token if entity was already seen, otherwise generates a new one."""
        clean_val = raw_value.strip()
        if clean_val in self.entity_to_token:
            return self.entity_to_token[clean_val]

        self.counters[entity_type] += 1
        token = entity_type.format_token(self.counters[entity_type])
        self.entity_to_token[clean_val] = token
        self.token_to_entity[token] = clean_val
        return token

    def _extract_names(self, text: str) -> List[str]:
        """Extracts PERSON entities via local spaCy NER or contextual regex fallback."""
        names: List[str] = []

        if _NLP is not None:
            doc = _NLP(text)
            for ent in doc.ents:
                if ent.label_ == "PERSON" and ent.text.strip() not in self._stopwords:
                    names.append(ent.text.strip())

        # Always run contextual trigger regex to catch names missed by small NER models
        for match in self._name_triggers.finditer(text):
            candidate = match.group(1).strip()
            words = candidate.split()
            valid_words = [w for w in words if w not in self._stopwords and not w.startswith("REDACTED")]
            if valid_words:
                names.append(" ".join(valid_words))

        # Sort longest first so full names ("John Doe") are replaced before first names ("John")
        return sorted(set(names), key=len, reverse=True)

    def scrub(self, text: str, custom_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Scrubs raw input text and returns the sanitized string along with audit telemetry.
        """
        if not text:
            return {
                "raw_input": "",
                "sanitized_text": "",
                "token_map": {},
                "pii_count": 0,
                "detected_entities": []
            }

        sanitized = text
        detected_entities: List[Dict[str, str]] = []

        # Step 1: Scrub structured entities via Regex
        # Order matters: EMAIL, PHONE, AMOUNT, FINANCIAL_ORG before CREDENTIAL so phone/amounts aren't caught as raw digits
        priority_order = [
            EntityType.EMAIL,
            EntityType.PHONE,
            EntityType.AMOUNT,
            EntityType.FINANCIAL_ORG,
            EntityType.CREDENTIAL,
        ]

        for etype in priority_order:
            pattern = REGEX_PATTERNS[etype]
            matches = list(pattern.finditer(sanitized))
            unique_matches = sorted({m.group(0) for m in matches}, key=len, reverse=True)

            for raw_match in unique_matches:
                token = self._get_or_create_token(raw_match, etype)
                sanitized = sanitized.replace(raw_match, token)
                detected_entities.append({
                    "type": etype.value,
                    "raw": raw_match,
                    "token": token
                })

        # Step 2: Scrub explicit custom names + Local NER names
        candidate_names = self._extract_names(sanitized)
        if custom_names:
            candidate_names = sorted(set(candidate_names + custom_names), key=len, reverse=True)

        for name in candidate_names:
            name_pattern = re.compile(rf"\b{re.escape(name)}\b")
            if name_pattern.search(sanitized):
                token = self._get_or_create_token(name, EntityType.NAME)
                sanitized = name_pattern.sub(token, sanitized)
                detected_entities.append({
                    "type": EntityType.NAME.value,
                    "raw": name,
                    "token": token
                })

        return {
            "raw_input": text,
            "sanitized_text": sanitized,
            "token_map": dict(self.token_to_entity),
            "pii_count": len(detected_entities),
            "detected_entities": detected_entities,
        }

    def reset_session(self) -> None:
        """Clears token mappings for a fresh session."""
        self.entity_to_token.clear()
        self.token_to_entity.clear()
        self.counters = {etype: 0 for etype in EntityType}
