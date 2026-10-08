import json
import re
from typing import Dict, Any, Optional, Tuple
from app.agents.state import AnalysisState

def parse_execution_stdout(stdout: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    parsed_json = None
    chart_path = None

    # Search for RESULT_JSON:
    if "RESULT_JSON:" in stdout:
        parts = stdout.split("RESULT_JSON:", 1)[1]
        # Look for the JSON block
        lines = parts.strip().split("\n")
        json_str_candidates = []
        for line in lines:
            if line.strip() == "CHART_PATH:":
                break
            json_str_candidates.append(line)
        json_text = "\n".join(json_str_candidates).strip()
        try:
            parsed_json = json.loads(json_text)
        except json.JSONDecodeError:
            # Try regex extraction for curly braces
            match = re.search(r"(\{.*\})", parts, re.DOTALL)
            if match:
                try:
                    parsed_json = json.loads(match.group(1))
                except Exception:
                    pass

    # Search for CHART_PATH:
    if "CHART_PATH:" in stdout:
        chart_parts = stdout.split("CHART_PATH:", 1)[1]
        chart_line = chart_parts.strip().split("\n")[0].strip()
        if chart_line and ("png" in chart_line or "jpg" in chart_line or "svg" in chart_line):
            chart_path = chart_line

    return parsed_json, chart_path

async def result_analyzer_node(state: AnalysisState) -> Dict[str, Any]:
    stdout = state.get("last_stdout", "")
    parsed_json, chart_path = parse_execution_stdout(stdout)

    if not parsed_json:
        # Fallback structured record from stdout if script printed raw stats
        parsed_json = {
            "status": "success",
            "raw_output": stdout.strip()[:1000]
        }

    return {
        "parsed_findings": parsed_json,
        "chart_path": chart_path,
        "status": "analyzed"
    }
