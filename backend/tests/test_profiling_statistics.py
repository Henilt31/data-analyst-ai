import pytest
import pandas as pd
import numpy as np
from app.services.profiling import ProfilingService

def test_numeric_summary_statistics():
    df = pd.DataFrame({
        "values": [10.0, 20.0, 30.0, 40.0, 50.0],
        "with_nulls": [1.0, 2.0, None, 4.0, None]
    })

    profiler = ProfilingService()
    profile = profiler.profile_dataframe(df)

    num_stats = profile["numeric_stats"]
    assert "values" in num_stats
    assert num_stats["values"]["min"] == 10.0
    assert num_stats["values"]["max"] == 50.0
    assert num_stats["values"]["mean"] == 30.0
    assert num_stats["values"]["median"] == 30.0
    assert num_stats["values"]["q25"] == 20.0
    assert num_stats["values"]["q75"] == 40.0
    assert num_stats["values"]["unique_count"] == 5

    missing = profile["missing_data"]
    assert missing["with_nulls"]["missing_count"] == 2
    assert missing["with_nulls"]["missing_percentage"] == 40.0

def test_categorical_and_datetime_statistics():
    df = pd.DataFrame({
        "status": ["active", "active", "active", "pending", "closed"],
        "timestamp": pd.date_range("2026-01-01", periods=5, freq="D")
    })

    profiler = ProfilingService()
    profile = profiler.profile_dataframe(df)

    cat_stats = profile["categorical_stats"]
    assert "status" in cat_stats
    assert cat_stats["status"]["unique_count"] == 3
    assert cat_stats["status"]["frequencies"]["active"] == 3
    assert cat_stats["status"]["frequencies"]["pending"] == 1

    dt_stats = profile["datetime_stats"]
    assert "timestamp" in dt_stats
    assert "2026-01-01" in dt_stats["timestamp"]["min_date"]
    assert "2026-01-05" in dt_stats["timestamp"]["max_date"]
    assert dt_stats["timestamp"]["temporal_range_days"] == 4
