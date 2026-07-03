# memory/investigation_memory.py
# ChromaDB-powered memory layer for Fake News Autopsy
# Stores past investigation results as vector embeddings
# so repeat/similar claims are served from cache instantly
# instead of running the full 50-second pipeline again

import os
import sys
import json
import chromadb
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class InvestigationMemory:
    """
    Vector memory store for completed investigations.

    How it works:
    1. Every completed investigation is stored in ChromaDB
       with the claim as the document and verdict as metadata
    2. Before running a new investigation, we check if a
       similar claim was already investigated (similarity search)
    3. If similarity > threshold, return cached result instantly
    4. This saves API calls and makes the app feel fast for demos
    """

    def __init__(self, persist_dir: str = None):
        # Store ChromaDB data in project root/chroma_store
        if persist_dir is None:
            persist_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "chroma_store"
            )

        os.makedirs(persist_dir, exist_ok=True)

        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_dir)

        # Get or create the investigations collection
        self.collection = self.client.get_or_create_collection(
            name="investigations",
            metadata={"description": "Fake News Autopsy investigation results"}
        )

        print(f"📦 Memory initialized — {self.collection.count()} past investigations loaded")

    def store_investigation(self, claim: str, result: dict) -> bool:
        """
        Stores a completed investigation in vector memory.
        ChromaDB automatically creates embeddings for similarity search.
        """
        try:
            verdict_data = result.get("verdict_results", {}).get("verdict_data", {})

            # Build a unique ID from claim + timestamp
            doc_id = f"inv_{abs(hash(claim))}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Store the full result as metadata (serialized)
            # ChromaDB has a 64KB metadata limit per document
            # so we store only the verdict data, not the full raw results
            metadata = {
                "claim": claim[:500],
                "verdict": verdict_data.get("verdict", "UNVERIFIED"),
                "confidence_score": str(verdict_data.get("confidence_score", 0)),
                "one_line_summary": verdict_data.get("one_line_summary", "")[:500],
                "reasoning": verdict_data.get("reasoning", "")[:1000],
                "recommended_action": verdict_data.get("recommended_action", "")[:500],
                "limitations": verdict_data.get("limitations", "")[:500],
                "supporting_evidence": json.dumps(
                    verdict_data.get("supporting_evidence", [])
                )[:1000],
                "investigated_at": datetime.now().isoformat()
            }

            self.collection.add(
                documents=[claim],
                metadatas=[metadata],
                ids=[doc_id]
            )

            print(f"💾 Investigation stored in memory (ID: {doc_id})")
            return True

        except Exception as e:
            print(f"⚠️ Memory storage failed: {e}")
            return False

    def find_similar(self, claim: str, similarity_threshold: float = 0.85) -> dict | None:
        """
        Searches memory for a similar past investigation.
        Returns cached result if similarity exceeds threshold, else None.

        Threshold guide:
        - 0.95+ = nearly identical claims only
        - 0.85  = same topic, slightly different wording (recommended)
        - 0.70  = broad topic match (too loose — may return wrong verdicts)
        """
        try:
            count = self.collection.count()
            if count == 0:
                return None  # Nothing stored yet

            results = self.collection.query(
                query_texts=[claim],
                n_results=min(1, count)  # get the single best match
            )

            if not results["documents"] or not results["documents"][0]:
                return None

            # ChromaDB returns distances (lower = more similar)
            # Convert to similarity score (1 - distance)
            distance = results["distances"][0][0]
            similarity = 1 - distance

            print(f"🔍 Memory search: best match similarity = {similarity:.3f} (threshold: {similarity_threshold})")

            if similarity >= similarity_threshold:
                metadata = results["metadatas"][0][0]
                matched_claim = results["documents"][0][0]

                print(f"✅ Cache hit! Using stored investigation for similar claim")
                print(f"   Matched: '{matched_claim[:60]}...'")

                # Reconstruct verdict_data from stored metadata
                return {
                    "from_cache": True,
                    "similarity_score": round(similarity, 3),
                    "original_claim": matched_claim,
                    "verdict_data": {
                        "verdict": metadata.get("verdict", "UNVERIFIED"),
                        "confidence_score": int(metadata.get("confidence_score", 0)),
                        "one_line_summary": metadata.get("one_line_summary", ""),
                        "reasoning": metadata.get("reasoning", ""),
                        "recommended_action": metadata.get("recommended_action", ""),
                        "limitations": metadata.get("limitations", ""),
                        "supporting_evidence": json.loads(
                            metadata.get("supporting_evidence", "[]")
                        )
                    },
                    "investigated_at": metadata.get("investigated_at", "")
                }

            return None  # No sufficiently similar match

        except Exception as e:
            print(f"⚠️ Memory search failed: {e}")
            return None

    def get_all_investigations(self) -> list[dict]:
        """Returns all stored investigations — used for the history view in UI."""
        try:
            count = self.collection.count()
            if count == 0:
                return []

            results = self.collection.get(
                limit=50,
                include=["documents", "metadatas"]
            )

            investigations = []
            for doc, meta in zip(results["documents"], results["metadatas"]):
                investigations.append({
                    "claim": doc,
                    "verdict": meta.get("verdict", ""),
                    "confidence_score": meta.get("confidence_score", "0"),
                    "investigated_at": meta.get("investigated_at", "")
                })

            # Sort by most recent first
            investigations.sort(key=lambda x: x["investigated_at"], reverse=True)
            return investigations

        except Exception as e:
            print(f"⚠️ Memory retrieval failed: {e}")
            return []

    def count(self) -> int:
        """Returns number of stored investigations."""
        return self.collection.count()


# Quick test
if __name__ == "__main__":
    memory = InvestigationMemory()

    # Simulate storing a result
    fake_result = {
        "verdict_results": {
            "verdict_data": {
                "verdict": "FALSE",
                "confidence_score": 95,
                "one_line_summary": "COVID-19 vaccines do not contain microchips.",
                "reasoning": "Multiple credible medical institutions debunk this claim.",
                "recommended_action": "Do not share this claim.",
                "limitations": "Timeline data was limited.",
                "supporting_evidence": ["Mayo Clinic explicitly debunks this", "No scientific evidence exists"]
            }
        }
    }

    print("\n--- Storing investigation ---")
    memory.store_investigation("COVID-19 vaccines contain microchips", fake_result)

    print(f"\n--- Memory now has {memory.count()} investigations ---")

    print("\n--- Testing similarity search (exact match) ---")
    cached = memory.find_similar("COVID-19 vaccines contain microchips")
    if cached:
        print(f"Cache hit! Verdict: {cached['verdict_data']['verdict']}")
        print(f"Similarity: {cached['similarity_score']}")

    print("\n--- Testing similarity search (paraphrased claim) ---")
    cached2 = memory.find_similar("Do COVID vaccines have microchips in them?")
    if cached2:
        print(f"Cache hit! Verdict: {cached2['verdict_data']['verdict']}")
        print(f"Similarity: {cached2['similarity_score']}")
    else:
        print("No cache hit for paraphrased claim")