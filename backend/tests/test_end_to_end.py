import pytest
import io
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base
from app.db.repositories import DatasetRepository
from app.services.profiling import profiling_service
from app.services.sandbox import sandbox_service
from app.agents.graph import analysis_graph
from app.api.reports import generate_markdown_report

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def e2e_db():
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
async def test_full_autonomous_eda_pipeline_lifecycle(e2e_db, tmp_path: Path):
    # Step 1: Ingestion & Validation
    dataset_file = tmp_path / "e2e_customers.csv"
    dataset_file.write_text(
        "customer_id,age,annual_income,spending_score,membership_years\n"
        "C01,19,15000,39,1\n"
        "C02,21,15000,81,2\n"
        "C03,20,16000,6,1\n"
        "C04,23,16000,77,3\n"
        "C05,31,17000,40,4\n"
        "C06,22,17000,76,2\n"
        "C07,35,18000,6,5\n"
        "C08,23,18000,94,1\n"
        "C09,64,19000,3,10\n"
        "C10,30,19000,72,3\n",
        encoding="utf-8"
    )

    dataset_id = str(uuid.uuid4())
    repo = DatasetRepository(e2e_db)
    
    dataset = await repo.create_dataset(
        id=dataset_id,
        original_filename="e2e_customers.csv",
        stored_path=str(dataset_file),
        file_type="csv",
        file_size=len(dataset_file.read_bytes())
    )
    assert dataset.id == dataset_id

    # Step 2: Deterministic Profiling
    profile_data = profiling_service.profile_file(str(dataset_file), "csv")
    assert profile_data["shape"]["rows"] == 10
    assert profile_data["shape"]["columns"] == 5
    assert "annual_income" in profile_data["numeric_stats"]
    assert profile_data["numeric_stats"]["annual_income"]["mean"] == 17000.0

    profile = await repo.save_profile(dataset_id, profile_data)
    assert profile.dataset_id == dataset_id

    # Step 3: Research Question Generation & Persistence
    questions_spec = [
        {
            "question": "What is the relationship between annual income and spending score?",
            "rationale": "Identify high-value customer clusters for promotional targeting.",
            "columns": ["annual_income", "spending_score"],
            "category": "correlation"
        }
    ]
    saved_questions = await repo.create_research_questions(dataset_id, questions_spec)
    assert len(saved_questions) == 1
    target_q = saved_questions[0]

    # Step 4: Autonomous Analysis via LangGraph Pipeline
    run_id = str(uuid.uuid4())
    await repo.create_analysis_run(run_id, target_q.id)

    initial_state = {
        "dataset_id": dataset_id,
        "question_id": target_q.id,
        "run_id": run_id,
        "question": target_q.question,
        "columns_involved": target_q.columns_involved,
        "category": target_q.category,
        "schema_info": profile.schema_info,
        "profile_info": profile.numeric_stats,
        "dataset_path": str(dataset_file),
        "file_type": "csv",
        "current_attempt": 0,
        "max_attempts": 3,
        "current_code": "",
        "execution_history": [],
        "last_exit_code": None,
        "last_stdout": None,
        "last_stderr": None,
        "last_duration_ms": None,
        "last_failure_type": None,
        "last_output_files": [],
        "parsed_findings": None,
        "insight": None,
        "visualization": None,
        "status": "started"
    }

    final_state = await analysis_graph.ainvoke(initial_state)

    # Verify execution outcome
    assert final_state["status"] in ["success", "completed"]
    assert final_state["current_attempt"] >= 1
    assert len(final_state["execution_history"]) >= 1
    assert final_state["last_exit_code"] == 0
    assert final_state["insight"] is not None
    assert final_state["insight"]["takeaway"] is not None
    assert final_state["visualization"] is not None
    assert final_state["visualization"]["chart_path"] is not None

    # Step 5: Save Run Results to Repository
    saved_run = await repo.save_run_results(run_id, final_state)
    assert saved_run.status in ["success", "completed"]
    assert saved_run.insight is not None
    assert saved_run.visualization is not None

    # Step 6: Analytical Report Assembly
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload
    from app.db.models import Dataset, ResearchQuestion, AnalysisRun

    stmt = (
        select(Dataset)
        .options(
            selectinload(Dataset.profile),
            selectinload(Dataset.questions).selectinload(ResearchQuestion.runs).selectinload(AnalysisRun.insight),
            selectinload(Dataset.questions).selectinload(ResearchQuestion.runs).selectinload(AnalysisRun.visualization),
        )
        .where(Dataset.id == dataset_id)
    )
    result = await e2e_db.execute(stmt)
    loaded_ds = result.scalars().first()
    markdown_report = generate_markdown_report(loaded_ds, loaded_ds.profile, loaded_ds.questions)

    assert "# Dataset Analysis Report: e2e_customers.csv" in markdown_report
    assert "## Executive Summary" in markdown_report
    assert "## Data Quality Findings" in markdown_report
    assert "## Findings" in markdown_report
    assert "## Key Takeaways" in markdown_report
    assert target_q.question in markdown_report
    assert final_state["insight"]["text"] in markdown_report
