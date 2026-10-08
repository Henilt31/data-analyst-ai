import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import chromadb
from app.config import settings
from app.rag.embeddings import embedding_service

class ChromaStore:
    def __init__(self, persist_dir: str = settings.RAG_PERSIST_DIR):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            name="historical_datasets",
            metadata={"description": "Structural representations of previously analyzed datasets"}
        )

    def add_dataset_analysis(
        self,
        dataset_id: str,
        structural_representation: str,
        research_questions: List[Dict[str, Any]],
        successful_insights: List[Dict[str, Any]]
    ):
        embedding = embedding_service.encode([structural_representation])[0]
        metadata = {
            "dataset_id": dataset_id,
            "research_questions": json.dumps(research_questions),
            "successful_insights": json.dumps(successful_insights)
        }
        self.collection.upsert(
            ids=[dataset_id],
            embeddings=[embedding],
            documents=[structural_representation],
            metadatas=[metadata]
        )

    def query_similar(self, query_representation: str, n_results: int = 2) -> List[Dict[str, Any]]:
        count = self.collection.count()
        if count == 0:
            return []
        
        n_results = min(n_results, count)
        embedding = embedding_service.encode([query_representation])[0]
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )
        
        matches = []
        if results and results.get("metadatas") and results["metadatas"][0]:
            for meta in results["metadatas"][0]:
                matches.append({
                    "dataset_id": meta.get("dataset_id"),
                    "research_questions": json.loads(meta.get("research_questions", "[]")),
                    "successful_insights": json.loads(meta.get("successful_insights", "[]"))
                })
        return matches

chroma_store = ChromaStore()
