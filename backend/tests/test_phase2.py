import pytest
import io
import pandas as pd
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

@pytest.mark.anyio
async def test_upload_invalid_file():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        file_content = b"random executable content"
        res = await ac.post(
            "/datasets",
            files={"file": ("malicious.exe", file_content, "application/octet-stream")}
        )
        assert res.status_code == 400
        assert "Unsupported file format" in res.json()["detail"]

@pytest.mark.anyio
async def test_upload_csv():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        csv_data = "id,name,value\n1,Alice,100\n2,Bob,200\n3,Charlie,300\n"
        res = await ac.post(
            "/datasets",
            files={"file": ("test_sales.csv", csv_data.encode("utf-8"), "text/csv")}
        )
        assert res.status_code == 201
        data = res.json()
        assert data["original_filename"] == "test_sales.csv"
        assert data["file_type"] == "csv"
        assert data["file_size"] == len(csv_data)
        assert data["status"] in ["uploaded", "profiled"]
        assert "id" in data
        
        dataset_id = data["id"]
        get_res = await ac.get(f"/datasets/{dataset_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == dataset_id

@pytest.mark.anyio
async def test_upload_json():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        json_data = '[{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]'
        res = await ac.post(
            "/datasets",
            files={"file": ("data.json", json_data.encode("utf-8"), "application/json")}
        )
        assert res.status_code == 201
        data = res.json()
        assert data["original_filename"] == "data.json"
        assert data["file_type"] == "json"

@pytest.mark.anyio
async def test_upload_parquet():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        parquet_bytes = buf.getvalue()

        res = await ac.post(
            "/datasets",
            files={"file": ("data.parquet", parquet_bytes, "application/octet-stream")}
        )
        assert res.status_code == 201
        data = res.json()
        assert data["original_filename"] == "data.parquet"
        assert data["file_type"] == "parquet"

@pytest.mark.anyio
async def test_upload_excel():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        df = pd.DataFrame({"metric": [10.5, 20.2], "label": ["Q1", "Q2"]})
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        excel_bytes = buf.getvalue()

        res = await ac.post(
            "/datasets",
            files={"file": ("report.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert res.status_code == 201
        data = res.json()
        assert data["original_filename"] == "report.xlsx"
        assert data["file_type"] == "xlsx"

@pytest.mark.anyio
async def test_list_datasets():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/datasets")
        assert res.status_code == 200
        datasets = res.json()
        assert isinstance(datasets, list)
        assert len(datasets) >= 4
