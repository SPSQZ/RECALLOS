# evaluation/test_pii_isolation.py
import sys
import os
import shutil

# Add root to python path so evaluation can import privacy_engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from privacy_engine.scrubber import PIIScrubber
from privacy_engine.rehydrator import PIIRehydrator
from privacy_engine.vector_store.chroma_client import ChromaMemoryClient


def test_pii_isolation_and_rehydration():
    scrubber = PIIScrubber()
    rehydrator = PIIRehydrator()

    test_prompts = [
        "Send $5,000 from my Chase account to John Doe at john.doe@example.com or phone +1-555-019-2834.",
        "My API key is sk-proj-123456789abcdefghijklmnopqrstuvwxyz and my bank routing number is 987654321.",
        "Hey Itha Puneeth, transfer 10000 INR via HDFC Bank."
    ]

    print("=== 1. Running RecallOS Privacy Isolation & Rehydration Tests ===")
    
    for i, prompt in enumerate(test_prompts, 1):
        # 1. Scrub input
        result = scrubber.scrub(prompt)
        sanitized = result["sanitized_text"]
        token_map = result["token_map"]

        # 2. Assert zero raw PII keywords leaked into sanitized text
        assert "john.doe@example.com" not in sanitized, f"Test {i} Failed: Email leaked!"
        assert "+1-555-019-2834" not in sanitized, f"Test {i} Failed: Phone leaked!"
        assert "John Doe" not in sanitized, f"Test {i} Failed: Name leaked!"
        assert "sk-proj-123456789abcdefghijklmnopqrstuvwxyz" not in sanitized, f"Test {i} Failed: API Key leaked!"
        assert "987654321" not in sanitized, f"Test {i} Failed: Routing number leaked!"
        assert "Itha Puneeth" not in sanitized, f"Test {i} Failed: Name leaked!"

        # 3. Simulate LLM response containing tokens and rehydrate
        mock_llm_response = f"Sure! I have processed your request securely. Referenced tokens: {list(token_map.keys())}."
        rehydrated = rehydrator.rehydrate(mock_llm_response, token_map)

        print(f"\n[Test Case {i}]")
        print(f"  Raw Input     : {prompt}")
        print(f"  Sanitized     : {sanitized}")
        print(f"  Items Guarded : {result['pii_count']}")
        print(f"  Rehydrated    : {rehydrated}")

    print("\n✅ All Privacy Isolation & Rehydration tests passed successfully!")


def test_vector_store_and_memory_lifecycle():
    print("\n=== 2. Running Local Vector Store & Memory Lifecycle Tests ===")
    test_db_path = "./test_local_chromadb"
    client = ChromaMemoryClient(persist_directory=test_db_path, collection_name="test_memories")
    client.purge_all()

    # 1. Add sanitized memories
    mem1 = client.add_memory(
        text="User prefers transferring funds via [REDACTED_FINANCIAL_ORG_1] to [REDACTED_NAME_1].",
        category="preference",
        project_id="finance_ops"
    )
    print(f"  Added Memory 1: {mem1['id']} | Conflict: {mem1['conflict_detected']}")
    assert mem1["id"].startswith("mem_")

    # 2. Semantic search verification
    results = client.search_memories(query="transferring funds bank preference", top_k=1)
    assert len(results) == 1, "Expected 1 search result from vector store!"
    print(f"  Top Search Hit: '{results[0]['text']}' (Score: {results[0]['score']})")

    # 3. Conflict detection & superseding
    mem2 = client.add_memory(
        text="User prefers transferring funds via [REDACTED_FINANCIAL_ORG_1] to [REDACTED_NAME_1].",
        category="preference",
        project_id="finance_ops"
    )
    print(f"  Added Memory 2 (Duplicate): {mem2['id']} | Conflict Detected: {mem2['conflict_detected']} (with {mem2['conflicting_memory_id']})")
    assert mem2["conflict_detected"] is True

    # Mark first memory as superseded
    assert client.mark_superseded(mem1["id"]) is True
    active_memories = client.list_all_memories(include_superseded=False)
    assert len(active_memories) == 1 and active_memories[0]["id"] == mem2["id"]
    print(f"  Active Memories After Superseding: {len(active_memories)}")

    # Cleanup test directory
    client.purge_all()
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path, ignore_errors=True)

    print("✅ All Local Vector Store & Memory Lifecycle tests passed successfully!")


if __name__ == "__main__":
    test_pii_isolation_and_rehydration()
    test_vector_store_and_memory_lifecycle()
