import json
from typing import Dict, Any, List
from app.rag.store import chroma_store

class DatasetRetriever:
    def create_synthetic_representation(self, profile: Dict[str, Any]) -> str:
        """
        Creates a synthetic dataset representation using ONLY schema, column names,
        dtypes, and general structural metadata.
        NEVER embeds raw sensitive dataset rows.
        """
        schema_info = profile.get("schema", profile.get("schema_info", {}))
        columns = list(schema_info.keys())
        dtypes = [f"{col}: {info.get('dtype', 'unknown')} ({info.get('semantic_type', 'unknown')})" 
                  for col, info in schema_info.items()]
        
        rep = (
            f"Dataset Structure Overview:\n"
            f"Total Features: {len(columns)}\n"
            f"Feature Columns: {', '.join(columns)}\n"
            f"Data Types and Roles:\n" + "\n".join(dtypes)
        )
        return rep

    def index_completed_dataset(
        self,
        dataset_id: str,
        profile: Dict[str, Any],
        research_questions: List[Dict[str, Any]],
        successful_insights: List[Dict[str, Any]]
    ):
        rep = self.create_synthetic_representation(profile)
        chroma_store.add_dataset_analysis(
            dataset_id=dataset_id,
            structural_representation=rep,
            research_questions=research_questions,
            successful_insights=successful_insights
        )

    def retrieve_similar_analyses(self, profile: Dict[str, Any], top_k: int = 2) -> List[Dict[str, Any]]:
        rep = self.create_synthetic_representation(profile)
        return chroma_store.query_similar(rep, n_results=top_k)

dataset_retriever = DatasetRetriever()
