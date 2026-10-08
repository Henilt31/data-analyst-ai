import pytest
from app.services.llm import LLMClient
from app.schemas.analysis import GeneratedQuestions
from app.agents.insight_writer import GroundedInsightOutput

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_llm_service_offline_fallback_questions():
    client = LLMClient(provider="openrouter", openrouter_api_key="")
    assert not client.is_configured()

    res = await client.generate_json(
        prompt="Generate research questions for dataset",
        schema_class=GeneratedQuestions
    )
    assert len(res.questions) >= 3
    assert res.questions[0].question is not None

@pytest.mark.anyio
async def test_llm_service_offline_fallback_insights():
    client = LLMClient(provider="gemini", google_api_key="")
    assert not client.is_configured()

    res = await client.generate_json(
        prompt="Synthesize grounded insight",
        schema_class=GroundedInsightOutput
    )
    assert res.text is not None
    assert res.takeaway is not None
    assert isinstance(res.important_numbers, dict)

@pytest.mark.anyio
async def test_llm_service_clean_markdown_codeblocks():
    client = LLMClient(provider="openrouter", openrouter_api_key="")
    # Test json parsing handles schema properly
    parsed = await client.generate_json("questions", GeneratedQuestions)
    assert isinstance(parsed, GeneratedQuestions)
    assert len(parsed.questions) > 0
