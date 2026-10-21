import re
from typing import Dict, Tuple
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer

class PrivacyShield:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        
        phone_patterns = [
            Pattern(
                name="strict_phone",
                regex=r"\b(?:\+?\d{1,3}[-.\s]?)?(?:[6-9]\d{9}|\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4})\b",
                score=0.95
            )
        ]
        self.analyzer.registry.add_recognizer(
            PatternRecognizer(supported_entity="PHONE_NUMBER", patterns=phone_patterns)
        )

        credential_patterns = [
            Pattern(
                name="api_key",
                regex=r"\b(sk-[a-zA-Z0-9_-]{10,}|ghp_[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z-_]{35})\b",
                score=0.98
            ),
            Pattern(
                name="financial_id",
                regex=r"\b\d{11,18}\b",
                score=0.80
            )
        ]
        self.analyzer.registry.add_recognizer(
            PatternRecognizer(supported_entity="CREDENTIAL", patterns=credential_patterns)
        )

        self.forward_map: Dict[str, str] = {}
        self.reverse_map: Dict[str, str] = {}
        self.counters: Dict[str, int] = {}

    def sanitize(self, raw_text: str) -> Tuple[str, dict]:
        results = self.analyzer.analyze(
            text=raw_text,
            entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD", "CREDENTIAL"],
            language="en"
        )
        
        results = sorted(results, key=lambda x: (x.start, -x.score, -(x.end - x.start)))
        non_overlapping = []
        last_end = -1
        for res in results:
            if res.start >= last_end:
                non_overlapping.append(res)
                last_end = res.end

        for res in non_overlapping:
            original_val = raw_text[res.start:res.end]
            label = "NAME" if res.entity_type == "PERSON" else res.entity_type
            if original_val not in self.forward_map:
                self.counters[label] = self.counters.get(label, 0) + 1
                placeholder = f"[REDACTED_{label}_{self.counters[label]}]"
                self.forward_map[original_val] = placeholder
                self.reverse_map[placeholder] = original_val

        sanitized_text = raw_text
        for res in reversed(non_overlapping):
            original_val = raw_text[res.start:res.end]
            placeholder = self.forward_map[original_val]
            sanitized_text = sanitized_text[:res.start] + placeholder + sanitized_text[res.end:]

        for original_val in sorted(self.forward_map.keys(), key=len, reverse=True):
            placeholder = self.forward_map[original_val]
            pattern = re.compile(rf"(?<!\w){re.escape(original_val)}(?!\w)")
            sanitized_text = pattern.sub(placeholder, sanitized_text)

        audit_data = {
            "raw_input": raw_text,
            "sanitized_text": sanitized_text,
            "entities_redacted": len(self.forward_map),
            "mapping": dict(self.reverse_map)
        }
        return sanitized_text, audit_data

    def rehydrate(self, model_response: str) -> str:
        restored_text = model_response
        for placeholder in sorted(self.reverse_map.keys(), key=len, reverse=True):
            real_val = self.reverse_map[placeholder]
            clean_token = placeholder.strip("[]")
            pattern = re.compile(rf"\[?{re.escape(clean_token)}\]?(?!\d)", re.IGNORECASE)
            restored_text = pattern.sub(lambda _: real_val, restored_text)
        return restored_text

if __name__ == "__main__":
    shield = PrivacyShield()
    user_input = "Hi, I am Puneeth. My phone is 9876543210 and my key is sk-12345abcdef67890. Call Puneeth back."
    clean_text, audit = shield.sanitize(user_input)
    print("RAW INPUT     :", audit["raw_input"])
    print("SENT TO CLOUD :", audit["sanitized_text"])
    fake_cloud_reply = "Sure [REDACTED_NAME_1], I will text [REDACTED_PHONE_NUMBER_1] and secure key [REDACTED_CREDENTIAL_1]."
    final_output = shield.rehydrate(fake_cloud_reply)
    print("CLOUD REPLY   :", fake_cloud_reply)
    print("USER SEES     :", final_output)
