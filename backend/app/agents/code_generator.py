import json
import re
from typing import Dict, Any
from app.agents.state import AnalysisState
from app.services.llm import llm_client
from app.config import settings

def clean_code(raw_code: str) -> str:
    cleaned = raw_code.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:python)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()

async def generate_code_node(state: AnalysisState) -> Dict[str, Any]:
    question = state["question"]
    schema = state["schema_info"]
    file_type = state["file_type"]
    columns = state.get("columns_involved", [])
    category = state.get("category", "exploratory")

    system_prompt = (
        "You are an expert quantitative data scientist and Python software engineer. "
        "Your task is to write a clean, robust, self-contained Python analysis script to answer a specific research question.\n\n"
        "RULES FOR THE SCRIPT:\n"
        "1. GROUNDING PRINCIPLE: Never fabricate or hardcode numbers. Compute all metrics using pandas, numpy, or scipy from the dataset.\n"
        f"2. DATASET LOCATION: Load the dataset from 'data/input.{file_type}'. Use appropriate loader (pd.read_csv, pd.read_json, pd.read_parquet, or pd.read_excel).\n"
        "3. RESULTS OUTPUT: Output computed findings to stdout starting EXACTLY with the token 'RESULT_JSON:' followed on the next line by a valid JSON object string.\n"
        "   Example:\n"
        "   print('RESULT_JSON:')\n"
        "   print(json.dumps({\"status\": \"success\", \"metric\": \"churn_rate\", \"value\": 0.238}))\n"
        "4. VISUALIZATION OUTPUT: If a plot is analytically appropriate (bar, line, hist, box, scatter), save it to 'outputs/chart.png' and print:\n"
        "   print('CHART_PATH:')\n"
        "   print('outputs/chart.png')\n"
        "5. ONLY return executable python code within ```python ... ``` fences. No conversational chatter."
    )

    prompt = f"""
Research Question: {question}
Analysis Category: {category}
Relevant Columns: {columns}
Dataset Schema:
{json.dumps(schema, indent=2)}

Write the complete, self-contained Python analysis script.
"""

    raw_response = await llm_client.generate(prompt, system_prompt=system_prompt, model=settings.CODE_GENERATOR_MODEL)
    script = clean_code(raw_response)

    return {
        "current_code": script,
        "status": "running"
    }
