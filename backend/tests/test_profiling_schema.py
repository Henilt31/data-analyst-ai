import pytest
import pandas as pd
from app.services.profiling import ProfilingService

def test_schema_dtypes_and_semantic_types():
    df = pd.DataFrame({
        "user_id": [101, 102, 103, 104],
        "score": [85.5, 92.0, 78.5, 95.0],
        "category": ["A", "B", "A", "C"],
        "joined_at": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        "comment": ["Good job", "Needs improvement", "Excellent work", "Pass"]
    })

    profiler = ProfilingService()
    profile = profiler.profile_dataframe(df)

    schema = profile["schema_info"]
    assert "user_id" in schema
    assert "score" in schema
    assert "category" in schema
    assert "joined_at" in schema

    # Verify semantic inference
    assert schema["score"]["semantic_type"] == "numeric"
    assert schema["category"]["semantic_type"] == "categorical"
    assert schema["joined_at"]["semantic_type"] == "datetime"
    assert schema["user_id"]["semantic_type"] == "id"

def test_schema_unicode_and_special_characters():
    df = pd.DataFrame({
        "revenue (USD)": [1000.0, 2000.0],
        "tax_%": [15.0, 20.0],
        "nom_client": ["Alice", "Bob"]
    })

    profiler = ProfilingService()
    profile = profiler.profile_dataframe(df)

    schema = profile["schema_info"]
    assert "revenue (USD)" in schema
    assert "tax_%" in schema
    assert "nom_client" in schema
    assert profile["shape"]["columns"] == 3
    assert profile["shape"]["rows"] == 2
