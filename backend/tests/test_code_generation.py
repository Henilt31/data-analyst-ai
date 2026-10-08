import pytest
import ast
from app.agents.code_generator import clean_code, generate_code_node
from app.agents.state import AnalysisState

@pytest.fixture
def anyio_backend():
    return "asyncio"

def test_clean_code_strips_markdown_fences():
    fenced_code = "```python\nimport pandas as pd\nprint('hello')\n```"
    cleaned = clean_code(fenced_code)
    assert cleaned == "import pandas as pd\nprint('hello')"

    plain_code = "import numpy as np\nprint(123)"
    assert clean_code(plain_code) == plain_code

@pytest.mark.anyio
async def test_generate_code_node_structure():
    dummy_state: AnalysisState = {
        "dataset_id": "test_ds",
        "question_id": "test_q",
        "run_id": "test_run",
        "question": "What is the average employee satisfaction per department?",
        "columns_involved": ["department", "satisfaction"],
        "category": "segmentation",
        "schema_info": {"department": {"dtype": "object"}, "satisfaction": {"dtype": "float64"}},
        "profile_info": {},
        "dataset_path": "data/test.csv",
        "file_type": "csv",
        "current_attempt": 0,
        "max_attempts": 3,
        "current_code": "",
        "execution_history": [],
        "last_exit_code": None,
        "last_stdout": None,
        "last_stderr": None,
        "last_duration_ms": None,
        "last_failure_type": None,
        "last_output_files": [],
        "parsed_findings": None,
        "insight": None,
        "visualization": None,
        "status": "pending"
    }

    result = await generate_code_node(dummy_state)
    assert "current_code" in result
    code = result["current_code"]

    # Verify python syntax is valid AST
    parsed_ast = ast.parse(code)
    assert parsed_ast is not None
    assert "pd.read_" in code or "pandas" in code
