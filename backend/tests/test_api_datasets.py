import pytest
import io
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.main import app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def test_client():
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
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()

@pytest.mark.anyio
async def test_dataset_api_lifecycle(test_client):
    # 1. Upload CSV dataset
    csv_content = b"user_id,age,score,signup_date\n1,25,88.5,2023-01-01\n2,30,92.0,2023-01-02\n3,35,79.0,2023-01-03\n"
    files = {"file": ("test_users.csv", io.BytesIO(csv_content), "text/csv")}
    
    response = await test_client.post("/datasets", files=files)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    dataset_id = data["id"]
    assert data["original_filename"] == "test_users.csv"
    assert data["file_type"] == "csv"
    assert data["row_count"] == 3
    assert data["column_count"] == 4
    assert data["status"] == "profiled"

    # 2. List datasets
    list_resp = await test_client.get("/datasets")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(d["id"] == dataset_id for d in items)

    # 3. Get single dataset
    get_resp = await test_client.get(f"/datasets/{dataset_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == dataset_id

    # 4. Get dataset profile
    prof_resp = await test_client.get(f"/datasets/{dataset_id}/profile")
    assert prof_resp.status_code == 200
    profile = prof_resp.json()
    assert profile["dataset_id"] == dataset_id
    assert "schema_info" in profile
    assert "age" in profile["schema_info"]
    assert "numeric_stats" in profile
    assert "age" in profile["numeric_stats"]
    assert profile["numeric_stats"]["age"]["mean"] == 30.0

    # 5. Non-existent dataset 404
    missing_resp = await test_client.get("/datasets/non-existent-uuid")
    assert missing_resp.status_code == 404
