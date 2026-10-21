import re
from typing import Dict, Tuple
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer

class PrivacyShield:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        
        # Custom rules for API keys and Bank/Financial numbers
        custom_patterns = [
            Pattern(name="api_key", regex=r"(sk-[a-zA-Z0-9]{10,}|AIza[0-9A-Za-z-_]{35})", score=0.95),
            Pattern(name="financial_id", regex=r"\b\d{9,18}\b", score=0.85)
        ]
        self.analyzer.registry.add_recognizer(
            PatternRecognizer(supported_entity="CREDENTIAL", patterns=custom_patterns)
        )

        # Stores mappings locally on your device
        self.forward_map: Dict[str, str] = {}   # {"Puneeth": "[REDACTED_NAME_1]"}
        self.reverse_map: Dict[str, str] = {}   # {"[REDACTED_NAME_1]": "Puneeth"}
        self.counters: Dict[str, int] = {}

    def sanitize(self, raw_text: str) -> Tuple[str, dict]:
        """Replaces sensitive info with deterministic placeholders before cloud dispatch."""
        results = self.analyzer.analyze(
            text=raw_text,
            entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD", "CREDENTIAL"],
            language="en"
        )
        
        # Sort backwards so replacing text doesn't mess up character positions
        results = sorted(results, key=lambda x: (x.start, -x.end), reverse=True)
        sanitized_text = raw_text
        last_start = len(raw_text) + 1

        for res in results:
            if res.end > last_start:
                continue
            last_start = res.start
            
            original_val = raw_text[res.start:res.end]
            label = "NAME" if res.entity_type == "PERSON" else res.entity_type

            # Deterministic check: same word always gets the exact same placeholder
            if original_val not in self.forward_map:
                self.counters[label] = self.counters.get(label, 0) + 1
                placeholder = f"[REDACTED_{label}_{self.counters[label]}]"
                self.forward_map[original_val] = placeholder
                self.reverse_map[placeholder] = original_val
            else:
                placeholder = self.forward_map[original_val]

            sanitized_text = sanitized_text[:res.start] + placeholder + sanitized_text[res.end:]

        # Output needed by Member 4 for the Privacy Audit Log UI
        audit_data = {
            "raw_input": raw_text,
            "sanitized_text": sanitized_text
        }
        return sanitized_text, audit_data

    def rehydrate(self, model_response: str) -> str:
        """Puts the real names/numbers back into the response from Nebius."""
        restored_text = model_response
        for placeholder, real_val in self.reverse_map.items():
            clean_token = placeholder.strip("[]")
            pattern = re.compile(rf"\[?{re.escape(clean_token)}\]?", re.IGNORECASE)
            restored_text = pattern.sub(real_val, restored_text)
        return restored_text


# --- QUICK TEST ---
if __name__ == "__main__":
    shield = PrivacyShield()
    
    # 1. Test Egress (Sanitizing user input)
    user_input = "Hi, I am Puneeth. My phone is 9876543210 and my key is sk-12345abcdef67890. Call Puneeth back."
    clean_text, audit = shield.sanitize(user_input)
    
    print("RAW INPUT     :", audit["raw_input"])
    print("SENT TO CLOUD :", audit["sanitized_text"])
    
    # 2. Test Ingress (Re-hydrating cloud response)
    fake_cloud_reply = "Sure [REDACTED_NAME_1], I will text [REDACTED_PHONE_NUMBER_1] and secure key [REDACTED_CREDENTIAL_1]."
    final_output = shield.rehydrate(fake_cloud_reply)
    
    print("CLOUD REPLY   :", fake_cloud_reply)
    print("USER SEES     :", final_output)
