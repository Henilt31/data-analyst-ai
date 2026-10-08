import pytest
from app.agents.graph import check_execution_success, failed_end_node
from app.agents.state import AnalysisState

def test_routing_success_branches_to_analyzer():
    state: AnalysisState = {
        "status": "success",
        "current_attempt": 1,
        "max_attempts": 3
    } # type: ignore
    assert check_execution_success(state) == "result_analyzer"

def test_routing_failure_under_max_attempts_branches_to_corrector():
    state: AnalysisState = {
        "status": "failed",
        "current_attempt": 1,
        "max_attempts": 3
    } # type: ignore
    assert check_execution_success(state) == "code_corrector"

def test_routing_failure_at_max_attempts_terminates_cleanly():
    state: AnalysisState = {
        "status": "failed",
        "current_attempt": 3,
        "max_attempts": 3
    } # type: ignore
    assert check_execution_success(state) == "failed_end"

@pytest.mark.anyio
async def test_failed_end_node_marks_terminal_status():
    state: AnalysisState = {"status": "running"} # type: ignore
    result = await failed_end_node(state)
    assert result["status"] == "failed"
