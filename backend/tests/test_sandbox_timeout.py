import pytest
from app.services.sandbox import SandboxService

def test_sandbox_terminates_infinite_loop_on_timeout(tmp_path):
    # Instantiate sandbox with 2-second timeout for rapid test execution
    sandbox = SandboxService()
    sandbox.timeout = 2

    dataset_file = tmp_path / "input.csv"
    dataset_file.write_text("x\n1\n", encoding="utf-8")

    infinite_loop_code = """
import time
while True:
    time.sleep(0.1)
"""
    result = sandbox.execute_code(infinite_loop_code, str(dataset_file), "timeout_run", attempt=1)
    assert not result.is_success
    assert result.timed_out is True
    assert result.exit_code == 124
    assert result.failure_type == "timeout"
    assert "timed out after 2 seconds" in result.stderr
