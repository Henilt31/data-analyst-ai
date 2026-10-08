import pytest
from fastapi import HTTPException
from app.services.storage import StorageService, MAX_FILE_SIZE

def test_file_format_validation():
    storage = StorageService()

    # Valid extensions
    for ext in ["csv", "json", "xlsx", "parquet"]:
        detected = storage.validate_file(f"sample.{ext}")
        assert detected == ext

    # Case insensitivity
    assert storage.validate_file("SAMPLE.CSV") == "csv"

    # Unsupported format
    with pytest.raises(HTTPException) as exc_info:
        storage.validate_file("malicious.exe")
    assert exc_info.value.status_code == 400
    assert "Unsupported file format" in exc_info.value.detail

    # Missing extension
    with pytest.raises(HTTPException) as exc_info:
        storage.validate_file("no_extension")
    assert exc_info.value.status_code == 400

def test_file_size_limit_constant():
    assert MAX_FILE_SIZE == 100 * 1024 * 1024
