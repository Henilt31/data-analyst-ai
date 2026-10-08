import pytest
from app.rag.retriever import dataset_retriever

def test_rag_synthetic_representation_excludes_raw_data():
    sample_profile = {
        "shape": {"rows": 1000, "columns": 3},
        "schema_info": {
            "customer_id": {"dtype": "int64", "semantic_type": "id"},
            "tenure_months": {"dtype": "int64", "semantic_type": "numeric"},
            "churn_status": {"dtype": "object", "semantic_type": "categorical"}
        },
        "numeric_stats": {
            "tenure_months": {"mean": 24.5, "min": 1, "max": 72}
        }
    }

    rep = dataset_retriever.create_synthetic_representation(sample_profile)

    # Must contain column schema and statistical descriptions
    assert "tenure_months" in rep
    assert "churn_status" in rep
    # Must NOT contain raw row tuples or data dumps
    assert "Row" not in rep
    assert "1000" in rep or "numeric" in rep

def test_rag_indexing_and_similarity_retrieval():
    profile_a = {
        "schema_info": {
            "user_id": {"semantic_type": "id"},
            "monthly_fee": {"semantic_type": "numeric"},
            "churn": {"semantic_type": "categorical"}
        }
    }
    dataset_retriever.index_completed_dataset(
        dataset_id="ds_telecom_1",
        profile=profile_a,
        research_questions=[{"question": "How does monthly fee impact churn rate?"}],
        successful_insights=[{"text": "Customers with monthly fees over 80 are 2.3x more likely to churn."}]
    )

    # Query with a structurally similar dataset
    query_profile = {
        "schema_info": {
            "client_id": {"semantic_type": "id"},
            "monthly_fee": {"semantic_type": "numeric"},
            "churn": {"semantic_type": "categorical"}
        }
    }

    results = dataset_retriever.retrieve_similar_analyses(query_profile, top_k=1)
    assert len(results) > 0
    assert results[0]["dataset_id"] == "ds_telecom_1"
    assert "monthly fee" in results[0]["research_questions"][0]["question"].lower()

def test_rag_disabled_baseline():
    # If no matches or empty profile, retrieval degrades safely to empty list
    results = dataset_retriever.retrieve_similar_analyses({}, top_k=2)
    assert isinstance(results, list)
