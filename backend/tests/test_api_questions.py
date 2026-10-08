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
async def test_questions_api_lifecycle(test_env):
    client, session_factory = test_env
    ds_id = str(uuid.uuid4())

    # Seed dataset and profile in db
    async with session_factory() as session:
        repo = DatasetRepository(session)
        await repo.create_dataset(
            id=ds_id,
            original_filename="sample_metrics.csv",
            stored_path="data/datasets/sample.csv",
            file_type="csv",
            file_size=512
        )
        await repo.save_profile(ds_id, {
            "shape": {"rows": 50, "columns": 3},
            "schema_info": {
                "user_id": {"dtype": "int64", "semantic_type": "identifier"},
                "revenue": {"dtype": "float64", "semantic_type": "numeric"},
                "clicks": {"dtype": "int64", "semantic_type": "numeric"}
            },
            "missing_data": {"user_id": 0, "revenue": 0, "clicks": 0},
            "numeric_stats": {
                "revenue": {"mean": 120.5, "min": 10.0, "max": 450.0},
                "clicks": {"mean": 15.2, "min": 1, "max": 80}
            },
            "categorical_stats": {},
            "datetime_stats": {},
            "data_quality": {"duplicated_rows": 0},
            "correlations": {"revenue_clicks": 0.78}
        })

    # 1. Generate questions via POST
    gen_resp = await client.post(f"/datasets/{ds_id}/questions?rag_enabled=false")
    assert gen_resp.status_code == 201
    questions = gen_resp.json()
    assert isinstance(questions, list)
    assert len(questions) >= 1
    first_q = questions[0]
    assert "id" in first_q
    assert "question" in first_q
    assert "rationale" in first_q
    assert "columns_involved" in first_q

    # 2. Retrieve generated questions via GET
    get_resp = await client.get(f"/datasets/{ds_id}/questions")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert len(retrieved) == len(questions)
    assert retrieved[0]["id"] == first_q["id"]

    # 3. 404 on missing dataset
    missing_resp = await client.get("/datasets/non-existent-uuid/questions")
    assert missing_resp.status_code == 404
