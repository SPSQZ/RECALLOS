import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict
from privacy_shield import PrivacyShield

class LocalMemoryManager:
    def __init__(self, db_path: str = "./recallos_local_db"):
        print("[M3] Initializing Local ChromaDB Vector Store...")
        # Runs 100% locally on disk—no cloud database keys needed
        self.client = chromadb.PersistentClient(path=db_path)
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="personal_agent_memory",
            embedding_function=self.embed_fn
        )
        self.shield = PrivacyShield()

    def add_memory(self, doc_id: str, text: str, source: str = "user_note") -> bool:
        """Stores personal context (files, notes, logs) locally on-device."""
        self.collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[{"source": source}]
        )
        return True

    def search_memory_safely(self, query: str, top_k: int = 2) -> List[Dict]:
        """
        Retrieves relevant personal memories and automatically scrubs PII 
        via PrivacyShield before any data goes to Nebius Cloud.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        sanitized_memories = []
        if results and results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            ids = results["ids"][0]

            for doc_id, doc_text, meta in zip(ids, docs, metas):
                # Scrub PII from the stored memory before cloud dispatch
                clean_text, audit_payload = self.shield.sanitize(doc_text)
                sanitized_memories.append({
                    "id": doc_id,
                    "source": meta.get("source", "unknown"),
                    "cloud_safe_text": clean_text,
                    "audit": audit_payload
                })
        
        return sanitized_memories


# --- QUICK TEST ---
if __name__ == "__main__":
    memory_manager = LocalMemoryManager()

    # 1. Save sample personal memory (containing sensitive info)
    memory_manager.add_memory(
        "mem_01", 
        "Puneeth's electricity bill of ₹1,400 was paid using account 987654321012.", 
        source="finance_skill"
    )

    # 2. Search and verify automatic PII scrubbing on retrieved context
    safe_results = memory_manager.search_memory_safely("What bills were paid?")

    print("\n--- LOCAL MEMORY SEARCH & SCRUB TEST ---")
    for res in safe_results:
        print(f"Memory ID       : {res['id']}")
        print(f"Source Skill    : {res['source']}")
        print(f"Scrubbed for AI : {res['cloud_safe_text']}")
