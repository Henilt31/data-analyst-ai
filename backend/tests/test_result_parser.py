import pytest
from app.agents.result_analyzer import parse_execution_stdout

def test_parse_valid_result_json_and_chart():
    stdout = """
Initial output log line 1
Initial output log line 2
RESULT_JSON:
{"metric": "churn_rate", "value": 0.238, "count": 1000}
CHART_PATH:
outputs/churn_bar.png
Finished processing
"""
    parsed_json, chart_path = parse_execution_stdout(stdout)
    assert parsed_json is not None
    assert parsed_json["metric"] == "churn_rate"
    assert parsed_json["value"] == 0.238
    assert parsed_json["count"] == 1000
    assert chart_path == "outputs/churn_bar.png"

def test_parse_malformed_json_fails_safely():
    stdout = """
RESULT_JSON:
{not a valid json object
"""
    parsed_json, chart_path = parse_execution_stdout(stdout)
    assert parsed_json is None
    assert chart_path is None

def test_parse_missing_result_token_fails_safely():
    stdout = "Plain log output without any structured tokens."
    parsed_json, chart_path = parse_execution_stdout(stdout)
    assert parsed_json is None
    assert chart_path is None
