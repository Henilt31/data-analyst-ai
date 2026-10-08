import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.session import get_db
from app.db.repositories import DatasetRepository
from app.services.llm import llm_client
from app.services.profiling import profiling_service
from app.schemas.analysis import GeneratedQuestions, ResearchQuestionResponse

router = APIRouter(tags=["questions"])

@router.post("/datasets/{dataset_id}/questions", response_model=List[ResearchQuestionResponse], status_code=201)
async def generate_research_questions(
    dataset_id: str,
    rag_enabled: bool = Query(default=False),
    db: AsyncSession = Depends(get_db)
):
    repo = DatasetRepository(db)
    dataset = await repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile = await repo.get_profile(dataset_id)
    if not profile:
        profile_data = profiling_service.profile_file(dataset.stored_path, dataset.file_type)
        profile = await repo.save_profile(dataset_id, profile_data)

    # Prepare grounding profile context
    profile_summary = {
        "filename": dataset.original_filename,
        "file_type": dataset.file_type,
        "rows": dataset.row_count,
        "columns": dataset.column_count,
        "schema": profile.schema_info,
        "missing_data": profile.missing_data,
        "numeric_statistics": profile.numeric_stats,
        "categorical_statistics": profile.categorical_stats,
        "datetime_statistics": profile.datetime_stats,
        "data_quality_issues": profile.data_quality,
        "correlations": profile.correlations
    }

    # Optional RAG context if enabled
    rag_context = ""
    if rag_enabled:
        from app.rag.retriever import dataset_retriever
        retrieved_items = dataset_retriever.retrieve_similar_analyses(profile_summary)
        if retrieved_items:
            rag_context = f"\nRelevant past analysis patterns from similar datasets:\n{json.dumps(retrieved_items, indent=2)}\n"

    system_prompt = (
        "You are an expert autonomous data scientist. Given the deterministic statistical profile of a dataset, "
        "formulate deep, dataset-specific, rigorous research questions that uncover actionable patterns, anomalies, "
        "correlations, and segment differences. Do NOT invent columns. Focus strictly on existing variables."
    )

    prompt = f"""
Dataset Profile:
{json.dumps(profile_summary, indent=2)}
{rag_context}
Generate between 3 and 5 highly insightful research questions.
Each question must include:
- question: specific, testable hypothesis or exploratory question
- rationale: why this analysis matters analytically
- columns: list of exact column names from the dataset involved
- category: one of 'distribution', 'correlation', 'segmentation', 'outlier_analysis', 'temporal_trend'

Return JSON matching the schema:
{{
  "questions": [
    {{
      "question": "...",
      "rationale": "...",
      "columns": ["col1", "col2"],
      "category": "..."
    }}
  ]
}}
"""

    generated = await llm_client.generate_json(prompt, GeneratedQuestions, system_prompt=system_prompt)
    
    questions_dicts = [q.model_dump() for q in generated.questions]
    saved_questions = await repo.create_research_questions(dataset_id, questions_dicts)
    return saved_questions

@router.get("/datasets/{dataset_id}/questions", response_model=List[ResearchQuestionResponse])
async def get_dataset_questions(dataset_id: str, db: AsyncSession = Depends(get_db)):
    repo = DatasetRepository(db)
    dataset = await repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return await repo.get_research_questions(dataset_id)
