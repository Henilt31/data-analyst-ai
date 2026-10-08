import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base
from app.db.models import Dataset, DatasetProfile, ResearchQuestion, AnalysisRun, AnalysisAttempt, Insight, Visualization, Report
from app.db.repositories import DatasetRepository

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def async_session():
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
    async with session_factory() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.anyio
async def test_database_models_and_repository_lifecycle(async_session):
    ds_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    repo = DatasetRepository(async_session)

    # 1. Create Dataset
    dataset = await repo.create_dataset(
        id=ds_id,
        original_filename="test_db.csv",
        stored_path="data/datasets/test.csv",
        file_type="csv",
        file_size=1024
    )
    assert dataset.id == ds_id
    assert dataset.status == "uploaded"

    # 2. Save Profile
    profile_data = {
        "shape": {"rows": 100, "columns": 5},
        "schema_info": {"col1": {"dtype": "int64", "semantic_type": "numeric"}},
        "missing_data": {},
        "numeric_stats": {"col1": {"mean": 50.0}},
        "categorical_stats": {},
        "datetime_stats": {},
        "data_quality": {"duplicated_rows": 0},
        "correlations": {}
    }
    profile = await repo.save_profile(ds_id, profile_data)
    assert profile.dataset_id == ds_id

    # Verify dataset status updated to profiled
    updated_ds = await repo.get_dataset(ds_id)
    assert updated_ds.status == "profiled"
    assert updated_ds.row_count == 100
    assert updated_ds.column_count == 5

    # 3. Create Research Questions
    questions = await repo.create_research_questions(
        dataset_id=ds_id,
        questions=[
            {
                "question": "What is the distribution of col1?",
                "rationale": "Understand central tendency",
                "columns": ["col1"],
                "category": "distribution"
            }
        ]
    )
    assert len(questions) == 1
    target_q_id = questions[0].id
    assert questions[0].question == "What is the distribution of col1?"

    # 4. Create Run and Save Results
    run = await repo.create_analysis_run(run_id, target_q_id)
    assert run.id == run_id
    assert run.status == "running"

    final_state = {
        "status": "success",
        "current_attempt": 1,
        "execution_history": [
            {
                "attempt_number": 1,
                "exit_code": 0,
                "stdout": 'RESULT_JSON:\n{"val": 123}',
                "stderr": "",
                "duration_ms": 200,
                "status": "success",
                "failure_type": "none",
                "generated_code": "import pandas as pd\nprint(123)"
            }
        ],
        "insight": {
            "text": "col1 shows balanced normal distribution.",
            "evidence": {"mean": 50.0},
            "important_numbers": {"mean": 50.0},
            "takeaway": "Baseline established.",
            "caveats": "Small sample size."
        },
        "visualization": {
            "chart_type": "histogram",
            "chart_path": "outputs/col1_hist.png",
            "title": "col1 distribution",
            "data": {"mean": 50.0}
        }
    }
    saved_run = await repo.save_run_results(run_id, final_state)
    assert saved_run is not None
    assert saved_run.status == "success"

    # 5. Fetch and verify persistence & relations
    fetched_run = await repo.get_run(run_id)
    assert fetched_run is not None
    assert fetched_run.status == "success"
    assert len(fetched_run.attempts) == 1
    assert fetched_run.attempts[0].status == "success"
    assert fetched_run.attempts[0].generated_code is not None
    assert fetched_run.insight is not None
    assert fetched_run.insight.takeaway == "Baseline established."
    assert fetched_run.visualization is not None
    assert fetched_run.visualization.chart_type == "histogram"
