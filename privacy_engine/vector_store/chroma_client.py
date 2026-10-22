# privacy_engine/vector_store/chroma_client.py
import os
import uuid
import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from privacy_engine.vector_store.embeddings import LocalEmbeddingEngine

try:
    import chromadb
    _CHROMA_AVAILABLE = True
except Exception:
    _CHROMA_AVAILABLE = False


class ChromaMemoryClient:
    """
    Persistent local ChromaDB collection manager for RecallOS.
    Stores and retrieves semantic memories strictly on-device.
    """

    def __init__(
        self,
        persist_directory: str = "./local_chromadb",
        collection_name: str = "recallos_memories",
    ) -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedder = LocalEmbeddingEngine()

        self._use_chroma = _CHROMA_AVAILABLE
        self._fallback_store: Dict[str, Dict[str, Any]] = {}

        if self._use_chroma:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedder.chroma_embedding_function,
                metadata={"hnsw:space": "cosine"},
            )

    def add_memory(
        self,
        text: str,
        category: str = "fact",
        project_id: str = "default",
        source: str = "chat",
        memory_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Inserts or updates a memory in the local vector store and checks for conflicts.
        """
        mem_id = memory_id or f"mem_{uuid.uuid4().hex[:10]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Check for potential semantic conflicts before inserting
        existing_matches = self.search_memories(query=text, top_k=1, active_only=True)
        conflict_detected = False
        conflicting_id = None

        if existing_matches and existing_matches[0]["score"] >= 0.85:
            conflict_detected = True
            conflicting_id = existing_matches[0]["id"]

        metadata = {
            "category": str(category),
            "project_id": str(project_id),
            "source": str(source),
            "timestamp": timestamp,
            "superseded": False,
        }

        if self._use_chroma:
            self.collection.upsert(
                ids=[mem_id],
                documents=[text],
                metadatas=[metadata],
            )
        else:
            self._fallback_store[mem_id] = {
                "id": mem_id,
                "text": text,
                "embedding": self.embedder.embed_query(text),
                "metadata": metadata,
            }

        return {
            "id": mem_id,
            "text": text,
            "metadata": metadata,
            "conflict_detected": conflict_detected,
            "conflicting_memory_id": conflicting_id,
        }

    def search_memories(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        project_id: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search and returns cited memory items with relevance scores.
        """
        if not query or not query.strip():
            return []

        if self._use_chroma:
            total_count = self.collection.count()
            if total_count == 0:
                return []

            where_clauses: List[Dict[str, Any]] = []
            if active_only:
                where_clauses.append({"superseded": False})
            if category:
                where_clauses.append({"category": category})
            if project_id:
                where_clauses.append({"project_id": project_id})

            where_filter: Optional[Dict[str, Any]] = None
            if len(where_clauses) == 1:
                where_filter = where_clauses[0]
            elif len(where_clauses) > 1:
                where_filter = {"$and": where_clauses}

            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, total_count),
                where=where_filter,
            )

            memories: List[Dict[str, Any]] = []
            if results and results.get("ids") and results["ids"][0]:
                for i, mem_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i] if results.get("distances") else 0.0
                    # Convert cosine distance to similarity score in [0, 1]
                    score = round(max(0.0, 1.0 - float(distance)), 4)
                    meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                    memories.append({
                        "id": mem_id,
                        "text": results["documents"][0][i],
                        "score": score,
                        "metadata": meta,
                    })
            return memories

        # Fallback in-memory cosine search
        query_vec = self.embedder.embed_query(query)
        scored: List[Dict[str, Any]] = []
        for item in self._fallback_store.values():
            meta = item["metadata"]
            if active_only and meta.get("superseded", False):
                continue
            if category and meta.get("category") != category:
                continue
            if project_id and meta.get("project_id") != project_id:
                continue

            score = self._cosine_similarity(query_vec, item["embedding"])
            scored.append({
                "id": item["id"],
                "text": item["text"],
                "score": round(score, 4),
                "metadata": meta,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def mark_superseded(self, memory_id: str) -> bool:
        """
        Marks an outdated memory as superseded during conflict resolution
        (used by agent_core/tools/tool_memory.py).
        """
        if self._use_chroma:
            existing = self.collection.get(ids=[memory_id])
            if not existing or not existing.get("ids"):
                return False
            meta = existing["metadatas"][0] or {}
            meta["superseded"] = True
            self.collection.update(ids=[memory_id], metadatas=[meta])
            return True

        if memory_id in self._fallback_store:
            self._fallback_store[memory_id]["metadata"]["superseded"] = True
            return True
        return False

    def delete_memory(self, memory_id: str) -> bool:
        """Deletes a single memory by ID."""
        if self._use_chroma:
            self.collection.delete(ids=[memory_id])
            return True
        return self._fallback_store.pop(memory_id, None) is not None

    def list_all_memories(self, include_superseded: bool = False) -> List[Dict[str, Any]]:
        """Returns all stored memories for the /memories control center."""
        if self._use_chroma:
            if self.collection.count() == 0:
                return []
            where_filter = None if include_superseded else {"superseded": False}
            data = self.collection.get(where=where_filter)
            items = []
            for i, mem_id in enumerate(data.get("ids", [])):
                items.append({
                    "id": mem_id,
                    "text": data["documents"][i],
                    "metadata": data["metadatas"][i],
                })
            return items

        return [
            {"id": v["id"], "text": v["text"], "metadata": v["metadata"]}
            for v in self._fallback_store.values()
            if include_superseded or not v["metadata"].get("superseded", False)
        ]

    def purge_all(self) -> int:
        """Purges the entire local vector database (used by /settings)."""
        if self._use_chroma:
            count = self.collection.count()
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedder.chroma_embedding_function,
                metadata={"hnsw:space": "cosine"},
            )
            return count

        count = len(self._fallback_store)
        self._fallback_store.clear()
        return count

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
        norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
        return max(0.0, dot / (norm_a * norm_b))
