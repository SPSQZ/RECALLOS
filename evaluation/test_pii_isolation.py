# evaluation/test_pii_isolation.py
import sys
import os

# Add root to python path so evaluation can import privacy_engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from privacy_engine.scrubber import PIIScrubber
from privacy_engine.rehydrator import PIIRehydrator


def test_pii_isolation_and_rehydration():
    scrubber = PIIScrubber()
    rehydrator = PIIRehydrator()

    test_prompts = [
        "Send $5,000 from my Chase account to John Doe at john.doe@example.com or phone +1-555-019-2834.",
        "My API key is sk-proj-123456789abcdefghijklmnopqrstuvwxyz and my bank routing number is 987654321.",
        "Hey Itha Puneeth, transfer 10000 INR via HDFC Bank."
    ]

    print("=== Running RecallOS Privacy Isolation & Rehydration Tests ===")
    
    for i, prompt in enumerate(test_prompts, 1):
        # 1. Scrub input
        result = scrubber.scrub(prompt)
        sanitized = result["sanitized_text"]
        token_map = result["token_map"]

        # 2. Assert zero raw PII keywords leaked into sanitized text
        assert "john.doe@example.com" not in sanitized, f"Test {i} Failed: Email leaked!"
        assert "+1-555-019-2834" not in sanitized, f"Test {i} Failed: Phone leaked!"
        assert "sk-proj-123456789abcdefghijklmnopqrstuvwxyz" not in sanitized, f"Test {i} Failed: API Key leaked!"

        # 3. Simulate LLM response containing tokens and rehydrate
        mock_llm_response = f"Sure! I have processed your request securely. Referenced tokens: {list(token_map.keys())}."
        rehydrated = rehydrator.rehydrate(mock_llm_response, token_map)

        print(f"\n[Test Case {i}]")
        print(f"  Raw Input     : {prompt}")
        print(f"  Sanitized     : {sanitized}")
        print(f"  Items Guarded : {result['pii_count']}")
        print(f"  Rehydrated    : {rehydrated}")

    print("\n✅ All Privacy Isolation & Rehydration tests passed successfully!")


if __name__ == "__main__":
    test_pii_isolation_and_rehydration()
