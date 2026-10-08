import pytest
import ast
from app.agents.code_corrector import correct_code_node
from app.agents.state import AnalysisState

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_code_corrector_patches_traceback():
    failing_state: AnalysisState = {
        "dataset_id": "ds_err",
        "question_id": "q_err",
        "run_id": "run_corr",
        "question": "What is the average price of products?",
        "columns_involved": ["price"],
        "category": "distribution",
        "schema_info": {"price": {"dtype": "float64", "semantic_type": "numeric"}},
        "profile_info": {},
        "dataset_path": "data/input.csv",
        "file_type": "csv",
        "current_attempt": 1,
        "max_attempts": 3,
        "current_code": "import pandas as pd\ndf = pd.read_csv('data/input.csv')\nprint(df['non_existent'])",
        "execution_history": [],
        "last_exit_code": 1,
        "last_stdout": "",
        "last_stderr": "KeyError: 'non_existent'",
        "last_duration_ms": 120,
        "last_failure_type": "KeyError",
        "last_output_files": [],
        "parsed_findings": None,
        "insight": None,
        "visualization": None,
        "status": "running"
    }

    correction_result = await correct_code_node(failing_state)
    assert "current_code" in correction_result
    corrected_code = correction_result["current_code"]

    # Verify python syntax is valid AST
    parsed = ast.parse(corrected_code)
    assert parsed is not None
    assert len(corrected_code) > 20
