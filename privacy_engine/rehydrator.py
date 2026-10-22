# privacy_engine/rehydrator.py
import re
from typing import Dict, Any
from privacy_engine.entity_types import REDACTED_TOKEN_PATTERN


class PIIRehydrator:
    """
    Maps deterministic [REDACTED_<TYPE>_<INDEX>] tokens from LLM responses
    back to raw plaintext locally on the client device.
    """

    @staticmethod
    def rehydrate(masked_text: str, token_map: Dict[str, str]) -> str:
        """
        Replaces all [REDACTED_...] tokens in masked_text using token_map.
        token_map format: { "[REDACTED_NAME_1]": "Puneeth", ... }
        """
        if not masked_text or not token_map:
            return masked_text

        # Fast single-pass regex replacement for exact tokens
        def _replace_match(match: re.Match) -> str:
            token = match.group(0)
            return token_map.get(token, token)

        rehydrated = REDACTED_TOKEN_PATTERN.sub(_replace_match, masked_text)

        # Fallback pass in case the LLM altered token casing (e.g., [redacted_name_1])
        for token, raw_val in token_map.items():
            if token.lower() in rehydrated.lower() and token not in rehydrated:
                pattern = re.compile(re.escape(token), re.IGNORECASE)
                rehydrated = pattern.sub(raw_val, rehydrated)

        return rehydrated

    @staticmethod
    def rehydrate_with_report(masked_text: str, token_map: Dict[str, str]) -> Dict[str, Any]:
        """
        Rehydrates response and returns metadata for the Privacy Audit Panel.
        """
        if not masked_text:
            return {
                "masked_response": "",
                "rehydrated_response": "",
                "tokens_restored": 0,
            }

        found_tokens = [
            token for token in token_map.keys()
            if token.lower() in masked_text.lower()
        ]
        rehydrated_text = PIIRehydrator.rehydrate(masked_text, token_map)

        return {
            "masked_response": masked_text,
            "rehydrated_response": rehydrated_text,
            "tokens_restored": len(found_tokens),
        }
