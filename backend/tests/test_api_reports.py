import pytest
import uuid
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
async def test_report_generation_and_fetch_endpoints(test_env):
    client, session_factory = test_env
    ds_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    async with session_factory() as session:
        repo = DatasetRepository(session)
        # Create dataset
        await repo.create_dataset(
            id=ds_id,
            original_filename="customer_churn.csv",
            stored_path="data/datasets/churn.csv",
            file_type="csv",
            file_size=2048
        )
        # Create profile
        await repo.save_profile(ds_id, {
            "shape": {"rows": 500, "columns": 6},
            "schema_info": {"churn": {"dtype": "int64", "semantic_type": "boolean"}},
            "missing_data": {},
            "numeric_stats": {},
            "categorical_stats": {},
            "datetime_stats": {},
            "data_quality": {
                "duplicated_rows": 2,
                "constant_columns": [],
                "suspicious_null_columns": []
            },
            "correlations": {}
        })
        # Create question
        qs = await repo.create_research_questions(
            dataset_id=ds_id,
            questions=[{
                "question": "What is the primary factor driving customer churn?",
                "rationale": "Identify churn drivers",
                "columns": ["churn", "tenure"],
                "category": "classification"
            }]
        )
        q_id = qs[0].id

        # Create run with insight and visualization
        await repo.create_analysis_run(run_id, q_id)
        await repo.save_run_results(run_id, {
            "status": "success",
            "execution_history": [{
                "attempt_number": 1,
                "exit_code": 0,
                "stdout": 'RESULT_JSON: {"odds_ratio": 3.4}',
                "stderr": "",
                "duration_ms": 150,
                "status": "success",
                "failure_type": "none"
            }],
            "insight": {
                "text": "Tenure below 6 months has an odds ratio of 3.4 for customer churn.",
                "evidence": {"odds_ratio": 3.4},
                "important_numbers": {"odds_ratio": 3.4},
                "takeaway": "Early customer onboarding requires targeted retention interventions.",
                "caveats": "Observational data without randomized control trial."
            },
            "visualization": {
                "chart_type": "bar_chart",
                "chart_path": "outputs/churn_by_tenure.png",
                "title": "Churn Rate by Tenure",
                "data": {"odds_ratio": 3.4}
            }
        })

    # 1. Generate Report via POST
    post_resp = await client.post(f"/datasets/{ds_id}/report")
    assert post_resp.status_code == 201
    report_data = post_resp.json()
    assert report_data["dataset_id"] == ds_id
    assert "content" in report_data
    content = report_data["content"]
    assert "Executive Summary" in content
    assert "Data Quality Findings" in content
    assert "What is the primary factor driving customer churn?" in content
    assert "odds ratio of 3.4" in content
    assert "Early customer onboarding requires targeted retention interventions." in content
    assert "outputs/churn_by_tenure.png" in content

    # 2. Get Report via GET
    get_resp = await client.get(f"/datasets/{ds_id}/report")
    assert get_resp.status_code == 200
    fetched_data = get_resp.json()
    assert fetched_data["id"] == report_data["id"]
    assert fetched_data["content"] == content

    # 3. 404 for missing dataset
    missing_resp = await client.get("/datasets/non-existent-ds/report")
    assert missing_resp.status_code == 404
