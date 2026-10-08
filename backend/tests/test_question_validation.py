import pytest
from pydantic import ValidationError
from app.schemas.analysis import QuestionItem, GeneratedQuestions

def test_research_question_schema_validation():
    valid_data = {
        "question": "What is the relationship between age and account balance?",
        "rationale": "High balances may concentrate in older demographics.",
        "columns": ["age", "balance"],
        "category": "correlation"
    }
    item = QuestionItem.model_validate(valid_data)
    assert item.question == valid_data["question"]
    assert item.category == "correlation"
    assert "age" in item.columns

def test_generated_questions_batch_validation():
    batch = {
        "questions": [
            {
                "question": "How does churn rate differ across contract types?",
                "rationale": "Identifies high-risk customer segments.",
                "columns": ["contract_type", "churn"],
                "category": "segmentation"
            },
            {
                "question": "What is the distribution of monthly spend?",
                "rationale": "Examines central tendencies and dispersion.",
                "columns": ["monthly_spend"],
                "category": "distribution"
            }
        ]
    }
    gen = GeneratedQuestions.model_validate(batch)
    assert len(gen.questions) == 2
    assert gen.questions[0].category == "segmentation"

def test_invalid_question_schema():
    with pytest.raises(ValidationError):
        # Missing required field 'question'
        QuestionItem.model_validate({
            "rationale": "Missing question title",
            "columns": ["a", "b"]
        })
