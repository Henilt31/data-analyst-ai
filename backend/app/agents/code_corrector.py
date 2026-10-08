import json
import re
from typing import Dict, Any
from app.agents.state import AnalysisState
from app.agents.code_generator import clean_code
from app.services.llm import llm_client
from app.config import settings

async def correct_code_node(state: AnalysisState) -> Dict[str, Any]:
    question = state["question"]
    schema = state["schema_info"]
    current_code = state["current_code"]
    stderr = state.get("last_stderr", "")
    stdout = state.get("last_stdout", "")
    failure_type = state.get("last_failure_type", "unknown")
    attempt = state["current_attempt"]

    system_prompt = (
        "You are an expert Python debugging engineer. A previously generated data analysis script failed during execution.\n"
        "Your job is to inspect the code, traceback, and schema, identify the root cause, and return fully corrected Python code.\n\n"
        "DEBUGGING RULES:\n"
        "1. Fix the exact error shown in the traceback (e.g. KeyError, TypeError, ValueError, missing column, wrong dtype).\n"
        "2. Ensure the code handles NaNs/missing values safely.\n"
        "3. Ensure the script prints 'RESULT_JSON:' followed by a valid JSON object string.\n"
        "4. Return ONLY the complete corrected python code within ```python ... ``` fences. No explanations."
    )

    prompt = f"""
Research Question: {question}
Failure Type: {failure_type} (Attempt {attempt})

Previous Code that failed:
```python
{current_code}
```

Execution Traceback / Error:
{stderr}

Execution Stdout:
{stdout}

Dataset Schema:
{json.dumps(schema, indent=2)}

Provide the complete, corrected Python script.
"""

    raw_response = await llm_client.generate(prompt, system_prompt=system_prompt, model=settings.CODE_CORRECTOR_MODEL)
    corrected_script = clean_code(raw_response)

    return {
        "current_code": corrected_script
    }
