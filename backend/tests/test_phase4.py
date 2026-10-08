import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.analysis import GeneratedQuestions, QuestionItem
from app.services.llm import LLMClient

@pytest.fixture
def anyio_backend():
    return 'asyncio'

def test_question_schema_validation():
    valid_data = {
        "questions": [
            {
                "question": "Which customer segments have the highest churn rate?",
                "rationale": "High churn directly damages ARR.",
                "columns": ["tenure", "churn"],
                "category": "segmentation"
            }
        ]
    }
    validated = GeneratedQuestions.model_validate(valid_data)
    assert len(validated.questions) == 1
    assert validated.questions[0].category == "segmentation"
    assert validated.questions[0].columns == ["tenure", "churn"]

@pytest.mark.anyio
async def test_llm_generate_json_fallback():
    client = LLMClient()
    prompt = "Generate research questions for the churn dataset."
    result = await client.generate_json(prompt, GeneratedQuestions)
    assert isinstance(result, GeneratedQuestions)
    assert len(result.questions) >= 3
    for q in result.questions:
        assert len(q.question) > 5
        assert q.category is not None

@pytest.mark.anyio
async def test_api_generate_and_get_questions():
    csv_content = """customer_id,monthly_charges,total_charges,churn
C101,29.85,29.85,No
C102,56.95,1889.50,No
C103,53.85,108.15,Yes
C104,42.30,1840.75,No
C105,70.70,151.65,Yes
"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Upload dataset
        up_res = await ac.post(
            "/datasets",
            files={"file": ("telco_churn.csv", csv_content.encode("utf-8"), "text/csv")}
        )
        assert up_res.status_code == 201
        dataset_id = up_res.json()["id"]

        # 2. Generate questions
        q_gen_res = await ac.post(f"/datasets/{dataset_id}/questions")
        assert q_gen_res.status_code == 201
        questions = q_gen_res.json()
        assert isinstance(questions, list)
        assert len(questions) >= 3
        assert "question" in questions[0]
        assert "dataset_id" in questions[0]
        assert questions[0]["dataset_id"] == dataset_id

        # 3. Retrieve questions
        q_get_res = await ac.get(f"/datasets/{dataset_id}/questions")
        assert q_get_res.status_code == 200
        retrieved_questions = q_get_res.json()
        assert len(retrieved_questions) == len(questions)
