import pytest
import pandas as pd
from app.services.profiling import ProfilingService

def test_data_quality_signals():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 4],  # Row 4 is duplicated
        "constant_col": [42, 42, 42, 42, 42],
        "heavy_nulls": [1.0, None, None, None, None],
        "target_churn": ["yes", "no", "yes", "no", "no"]
    })

    profiler = ProfilingService()
    profile = profiler.profile_dataframe(df)

    quality = profile["data_quality"]
    assert quality["duplicated_rows"] == 1
    assert "constant_col" in quality["constant_columns"]
    assert "heavy_nulls" in quality["suspicious_null_columns"]
    assert any("target" in str(col).lower() or "churn" in str(col).lower() for col in quality["potential_target_columns"])

def test_correlation_matrix_computation():
    df = pd.DataFrame({
        "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        "y": [2.0, 4.0, 6.0, 8.0, 10.0],  # Perfect positive correlation (r = 1.0)
        "z": [5.0, 4.0, 3.0, 2.0, 1.0]   # Perfect negative correlation (r = -1.0)
    })

    profiler = ProfilingService()
    profile = profiler.profile_dataframe(df)

    corrs = profile["correlations"]
    assert "x" in corrs
    assert "y" in corrs["x"]
    assert corrs["x"]["y"] == 1.0
    assert corrs["x"]["z"] == -1.0
