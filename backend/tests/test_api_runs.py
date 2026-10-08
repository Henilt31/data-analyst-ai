import pytest
import uuid
from unittest.mock import AsyncMock, patch
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.db.repositories import DatasetRepository
from app.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def test_env():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, session_factory

    app.dependency_overrides.clear()
    await engine.dispose()

@pytest.mark.anyio
async def test_analysis_runs_api_endpoints(test_env):
    client, session_factory = test_env
    ds_id = str(uuid.uuid4())
    q_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    async with session_factory() as session:
        repo = DatasetRepository(session)
        await repo.create_dataset(
            id=ds_id,
            original_filename="revenue_metrics.csv",
            stored_path="data/datasets/metrics.csv",
            file_type="csv",
            file_size=1024
        )
        created_qs = await repo.create_research_questions(
            dataset_id=ds_id,
            questions=[{
                "question": "What is the correlation between marketing spend and revenue?",
                "rationale": "Evaluate ROI",
                "columns": ["marketing_spend", "revenue"],
                "category": "correlation"
            }]
        )
        actual_q_id = created_qs[0].id

    # Mock job_bus.run_question_pipeline to simulate autonomous pipeline execution
    async def mock_pipeline(question_id, dataset_id, run_id=None):
        async with session_factory() as s:
            r = DatasetRepository(s)
            await r.create_analysis_run(run_id, question_id)
            await r.save_run_results(run_id, {
                "status": "success",
                "execution_history": [{
                    "attempt_number": 1,
                    "exit_code": 0,
                    "stdout": 'RESULT_JSON: {"r_squared": 0.85}',
                    "stderr": "",
                    "duration_ms": 320,
                    "status": "success",
                    "failure_type": "none",
                    "generated_code": "import pandas as pd\nprint(0.85)"
                }],
                "insight": {
                    "text": "Strong positive correlation observed between marketing spend and revenue.",
                    "evidence": {"r_squared": 0.85},
                    "important_numbers": {"r_squared": 0.85},
                    "takeaway": "Marketing budget drives top-line revenue effectively.",
                    "caveats": "Attribution model assumes linear causality."
                },
                "visualization": {
                    "chart_type": "scatter_plot",
                    "chart_path": "outputs/scatter.png",
                    "title": "Marketing vs Revenue",
                    "data": {"r_squared": 0.85}
                }
            })

    with patch("app.api.runs.job_bus.run_question_pipeline", side_effect=mock_pipeline):
        # 1. Trigger analysis run
        post_resp = await client.post("/runs", json={"question_id": actual_q_id, "dataset_id": ds_id})
        assert post_resp.status_code == 202
        run_data = post_resp.json()
        assert "id" in run_data
        triggered_run_id = run_data["id"]
        assert run_data["status"] == "success"
        assert len(run_data["attempts"]) == 1
        assert run_data["attempts"][0]["status"] == "success"
        assert run_data["insight"]["takeaway"] == "Marketing budget drives top-line revenue effectively."
        assert run_data["visualization"]["chart_type"] == "scatter_plot"

        # 2. Get analysis run by ID
        get_run_resp = await client.get(f"/runs/{triggered_run_id}")
        assert get_run_resp.status_code == 200
        fetched_run = get_run_resp.json()
        assert fetched_run["id"] == triggered_run_id
        assert fetched_run["insight"]["evidence"] == {"r_squared": 0.85}

        # 3. Get individual insight
        insight_id = fetched_run["insight"]["id"]
        get_insight_resp = await client.get(f"/insights/{insight_id}")
        assert get_insight_resp.status_code == 200
        insight_body = get_insight_resp.json()
        assert insight_body["id"] == insight_id
        assert "Strong positive correlation" in insight_body["text"]

    # 4. Error cases: 404 for missing question, run, insight
    bad_post = await client.post("/runs", json={"question_id": "non-existent-q", "dataset_id": ds_id})
    assert bad_post.status_code == 404

    bad_run = await client.get("/runs/non-existent-run")
    assert bad_run.status_code == 404

    bad_insight = await client.get("/insights/999999")
    assert bad_insight.status_code == 404
