import json
import os
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any
from app.config import settings

class TelemetryService:
    def __init__(self, logs_dir: str = settings.LOGS_DIR):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.trials_file = self.logs_dir / "trials.jsonl"

    def classify_failure(self, exit_code: Optional[int], stdout: str, stderr: str, timed_out: bool = False) -> str:
        if timed_out or exit_code == 124 or "timed out" in stderr.lower():
            return "timeout"
        if "out of memory" in stderr.lower() or exit_code in [137, 9]:
            return "out-of-memory"
        if "KeyError:" in stderr:
            return "KeyError"
        if "TypeError:" in stderr:
            return "TypeError"
        if "ValueError:" in stderr:
            return "ValueError"
        if "json.decoder.JSONDecodeError" in stderr or "malformed json" in stderr.lower() or "RESULT_JSON not found" in stderr:
            return "malformed JSON"
        if "AttributeError:" in stderr or "DtypeWarning" in stderr or "incompatible dtype" in stderr.lower():
            return "dtype mismatch"
        if "docker" in stderr.lower() or "sandbox" in stderr.lower():
            return "sandbox failure"
        if exit_code != 0:
            match = re.search(r"(\w+Error):", stderr)
            if match:
                return match.group(1)
            return "unknown execution failure"
        return "none"

    def log_trial(
        self,
        dataset_id: str,
        question_id: str,
        run_id: str,
        attempt: int,
        status: str,
        failure_type: Optional[str] = None,
        duration_ms: int = 0,
        llm_model: Optional[str] = None,
        rag_enabled: bool = False,
        token_usage: Optional[Dict[str, Any]] = None
    ):
        trial_data = {
            "timestamp": time.time(),
            "dataset_id": dataset_id,
            "question_id": question_id,
            "run_id": run_id,
            "attempt": attempt,
            "status": status,
            "failure_type": failure_type,
            "duration_ms": duration_ms,
            "llm_model": llm_model or settings.CODE_GENERATOR_MODEL,
            "rag_enabled": rag_enabled,
            "token_usage": token_usage
        }

        with open(self.trials_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(trial_data) + "\n")

telemetry_service = TelemetryService()
