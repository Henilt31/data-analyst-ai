import pytest
import io
import pandas as pd
import numpy as np
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.profiling import profiling_service

@pytest.fixture
def anyio_backend():
    return 'asyncio'

def test_profiling_service_deterministic():
    # Construct test dataframe with numeric, categorical, datetime, missing values, duplicates, and correlation
    data = {
        "id": [101, 102, 103, 104, 105],
        "category": ["Electronics", "Clothing", "Electronics", "Clothing", None],
        "price": [100.0, 50.0, 200.0, 75.0, 150.0],
        "quantity": [2, 4, 1, 3, 2],
        "date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
        "constant_col": [1, 1, 1, 1, 1],
    }
    df = pd.DataFrame(data)
    profile = profiling_service.profile_dataframe(df)

    # Shape
    assert profile["shape"]["rows"] == 5
    assert profile["shape"]["columns"] == 6

    # Schema & semantic types
    assert profile["schema_info"]["id"]["semantic_type"] == "id"
    assert profile["schema_info"]["price"]["semantic_type"] == "numeric"
    assert profile["schema_info"]["category"]["semantic_type"] == "categorical"
    assert profile["schema_info"]["date"]["semantic_type"] == "datetime"

    # Missing data
    assert profile["missing_data"]["category"]["missing_count"] == 1
    assert profile["missing_data"]["category"]["missing_percentage"] == 20.0
    assert profile["missing_data"]["price"]["missing_count"] == 0

    # Numeric stats
    price_stats = profile["numeric_stats"]["price"]
    assert price_stats["min"] == 50.0
    assert price_stats["max"] == 200.0
    assert price_stats["mean"] == 115.0
    assert price_stats["median"] == 100.0
    assert price_stats["q25"] == 75.0
    assert price_stats["q75"] == 150.0

    # Categorical stats
    cat_stats = profile["categorical_stats"]["category"]
    assert cat_stats["unique_count"] == 2
    assert "Electronics" in cat_stats["top_values"]
    assert cat_stats["frequencies"]["Electronics"] == 2

    # Datetime stats
    dt_stats = profile["datetime_stats"]["date"]
    assert "2026-01-01" in dt_stats["min_date"]
    assert "2026-01-05" in dt_stats["max_date"]
    assert dt_stats["temporal_range_days"] == 4

    # Data Quality
    dq = profile["data_quality"]
    assert "constant_col" in dq["constant_columns"]
    assert "id" in dq["potential_id_columns"]
    assert "price" in dq["potential_target_columns"]

    # Correlations
    assert "price" in profile["correlations"]
    assert "quantity" in profile["correlations"]["price"]
    # Check price-quantity correlation is between -1 and 1
    corr_val = profile["correlations"]["price"]["quantity"]
    assert -1.0 <= corr_val <= 1.0

@pytest.mark.anyio
async def test_api_upload_and_get_profile():
    csv_content = """user_id,age,signup_date,churn,balance
1,25,2025-01-10,0,1200.50
2,38,2025-02-15,1,3400.00
3,42,2025-03-20,0,510.25
4,19,2025-04-05,0,890.00
5,55,2025-05-12,1,15400.75
"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        upload_res = await ac.post(
            "/datasets",
            files={"file": ("churn_data.csv", csv_content.encode("utf-8"), "text/csv")}
        )
        assert upload_res.status_code == 201
        dataset = upload_res.json()
        dataset_id = dataset["id"]
        assert dataset["row_count"] == 5
        assert dataset["column_count"] == 5
        assert dataset["status"] == "profiled"

        # Get profile endpoint
        prof_res = await ac.get(f"/datasets/{dataset_id}/profile")
        assert prof_res.status_code == 200
        profile = prof_res.json()
        assert profile["dataset_id"] == dataset_id
        assert "schema_info" in profile
        assert "age" in profile["numeric_stats"]
        assert profile["numeric_stats"]["age"]["min"] == 19
        assert profile["numeric_stats"]["age"]["max"] == 55
        assert "churn" in profile["data_quality"]["potential_target_columns"]
