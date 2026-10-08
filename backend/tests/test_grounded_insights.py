import pytest
from app.agents.insight_writer import insight_writer_node
from app.agents.state import AnalysisState

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_grounded_insight_incorporates_computed_findings():
    state: AnalysisState = {
        "dataset_id": "ds_test",
        "question_id": "q_test",
        "run_id": "run_grounding",
        "question": "What is the average customer acquisition cost?",
        "columns_involved": ["cac"],
        "category": "distribution",
        "schema_info": {"cac": {"dtype": "float64"}},
        "profile_info": {},
        "dataset_path": "data/input.csv",
        "file_type": "csv",
        "current_attempt": 1,
        "max_attempts": 3,
        "current_code": "",
        "execution_history": [],
        "last_exit_code": 0,
        "last_stdout": "RESULT_JSON:\n{\"mean_cac\": 47.85, \"sample_size\": 1200}",
        "last_stderr": "",
        "last_duration_ms": 350,
        "last_failure_type": "none",
        "last_output_files": [],
        "parsed_findings": {"mean_cac": 47.85, "sample_size": 1200},
        "insight": None,
        "visualization": None,
        "status": "running"
    }

    result = await insight_writer_node(state)
    assert "insight" in result
    insight = result["insight"]

    assert insight["text"] is not None
    assert len(insight["text"]) > 10
    assert insight["takeaway"] is not None
    assert "evidence" in insight
    assert "important_numbers" in insight
    assert result["status"] == "success"
