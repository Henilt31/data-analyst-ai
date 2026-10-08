import pytest
import json
from pathlib import Path
from app.services.telemetry import TelemetryService

def test_telemetry_failure_taxonomy_classification():
    telemetry = TelemetryService(logs_dir="data/test_logs")

    # 1. Timeout
    assert telemetry.classify_failure(124, "", "process timed out", timed_out=True) == "timeout"
    assert telemetry.classify_failure(124, "", "") == "timeout"

    # 2. Out of memory
    assert telemetry.classify_failure(137, "", "Killed (out of memory)") == "out-of-memory"

    # 3. Standard Python runtime errors
    assert telemetry.classify_failure(1, "", "KeyError: 'target_col'") == "KeyError"
    assert telemetry.classify_failure(1, "", "TypeError: 'float' object is not callable") == "TypeError"
    assert telemetry.classify_failure(1, "", "ValueError: could not convert string to float: 'a'") == "ValueError"

    # 4. JSON parsing / formatting failure
    assert telemetry.classify_failure(1, "", "json.decoder.JSONDecodeError: Expecting value: line 1 column 1") == "malformed JSON"
    assert telemetry.classify_failure(1, "", "RESULT_JSON not found in execution stdout") == "malformed JSON"

    # 5. Dtype mismatch
    assert telemetry.classify_failure(1, "", "AttributeError: 'Series' object has no attribute 'str'") == "dtype mismatch"

    # 6. Sandbox failure
    assert telemetry.classify_failure(1, "", "sandbox container daemon exited unexpectedly") == "sandbox failure"

    # 7. Regex generic exception fallback
    assert telemetry.classify_failure(1, "", "IndexError: list index out of range") == "IndexError"

    # 8. Success
    assert telemetry.classify_failure(0, "RESULT_JSON: {}", "") == "none"


def test_telemetry_trial_logging(tmp_path: Path):
    logs_dir = tmp_path / "logs"
    telemetry = TelemetryService(logs_dir=str(logs_dir))

    telemetry.log_trial(
        dataset_id="ds-telemetry-1",
        question_id="q-telemetry-1",
        run_id="run-telemetry-1",
        attempt=1,
        status="failure",
        failure_type="KeyError",
        duration_ms=450,
        llm_model="gemini-2.5-flash",
        rag_enabled=True,
        token_usage={"prompt": 500, "completion": 120}
    )

    trials_file = logs_dir / "trials.jsonl"
    assert trials_file.exists()

    with open(trials_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["dataset_id"] == "ds-telemetry-1"
        assert entry["question_id"] == "q-telemetry-1"
        assert entry["run_id"] == "run-telemetry-1"
        assert entry["attempt"] == 1
        assert entry["status"] == "failure"
        assert entry["failure_type"] == "KeyError"
        assert entry["duration_ms"] == 450
        assert entry["llm_model"] == "gemini-2.5-flash"
        assert entry["rag_enabled"] is True
        assert entry["token_usage"] == {"prompt": 500, "completion": 120}
