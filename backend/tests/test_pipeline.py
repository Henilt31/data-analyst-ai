import pytest
import os
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.sandbox import sandbox_service
from app.services.telemetry import telemetry_service
from app.agents.result_analyzer import parse_execution_stdout
from app.agents.graph import analysis_graph
from app.agents.state import AnalysisState
from app.rag.retriever import dataset_retriever

@pytest.fixture
def anyio_backend():
    return 'asyncio'

def test_failure_taxonomy_classification():
    # Timeout
    assert telemetry_service.classify_failure(124, "", "timed out", timed_out=True) == "timeout"
    # KeyError
    assert telemetry_service.classify_failure(1, "", "KeyError: 'revenue'") == "KeyError"
    # TypeError
    assert telemetry_service.classify_failure(1, "", "TypeError: unsupported operand") == "TypeError"
    # ValueError
    assert telemetry_service.classify_failure(1, "", "ValueError: could not convert string") == "ValueError"
    # Malformed JSON
    assert telemetry_service.classify_failure(0, "Not json", "RESULT_JSON not found") == "malformed JSON"

def test_result_parser_grounding():
    sample_stdout = """
Processing dataset...
Calculating churn rates...
RESULT_JSON:
{"status": "success", "metric": "churn_rate", "value": 0.238, "group": "month-to-month"}
CHART_PATH:
outputs/chart.png
"""
    parsed_json, chart_path = parse_execution_stdout(sample_stdout)
    assert parsed_json is not None
    assert parsed_json["metric"] == "churn_rate"
    assert parsed_json["value"] == 0.238
    assert chart_path == "outputs/chart.png"

def test_sandbox_execution_real_code(tmp_path):
    # Create test input dataset
    test_csv = tmp_path / "input.csv"
    test_csv.write_text("x,y\n10,20\n30,40\n", encoding="utf-8")

    code = """
import pandas as pd
import json

df = pd.read_csv('data/input.csv')
total = int(df['x'].sum())
print('RESULT_JSON:')
print(json.dumps({"sum_x": total}))
"""
    result = sandbox_service.execute_code(code, str(test_csv), run_id="test_run", attempt=1)
    assert result.is_success
    assert result.exit_code == 0
    assert "RESULT_JSON:" in result.stdout
    assert '"sum_x": 40' in result.stdout

def test_sandbox_failure_and_traceback_capture(tmp_path):
    test_csv = tmp_path / "input.csv"
    test_csv.write_text("col_a,col_b\n1,2\n", encoding="utf-8")

    failing_code = """
import pandas as pd
df = pd.read_csv('data/input.csv')
print(df['non_existent_column'])
"""
    result = sandbox_service.execute_code(failing_code, str(test_csv), run_id="test_fail", attempt=1)
    assert not result.is_success
    assert result.exit_code != 0
    assert "KeyError" in result.stderr
    assert result.failure_type == "KeyError"

def test_rag_synthetic_representation_and_retrieval():
    dummy_profile = {
        "schema": {
            "customer_id": {"dtype": "int64", "semantic_type": "id"},
            "monthly_charges": {"dtype": "float64", "semantic_type": "numeric"},
            "churn": {"dtype": "object", "semantic_type": "categorical"}
        }
    }
    # Verify no raw rows are present in representation
    rep = dataset_retriever.create_synthetic_representation(dummy_profile)
    assert "monthly_charges" in rep
    assert "customer_id" in rep
    assert "Row" not in rep

    # Index
    dataset_retriever.index_completed_dataset(
        dataset_id="test_ds_1",
        profile=dummy_profile,
        research_questions=[{"question": "How does charge correlate with churn?"}],
        successful_insights=[{"text": "Higher charges correlate with churn."}]
    )

    # Retrieve
    matches = dataset_retriever.retrieve_similar_analyses(dummy_profile, top_k=1)
    assert len(matches) > 0
    assert matches[0]["dataset_id"] == "test_ds_1"

@pytest.mark.anyio
async def test_full_autonomous_eda_workflow():
    csv_content = """department,employees,budget,satisfaction
Engineering,50,500000,4.2
Sales,80,400000,3.8
Marketing,30,250000,4.1
HR,15,100000,3.5
"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Upload dataset
        up_res = await ac.post(
            "/datasets",
            files={"file": ("company_eda.csv", csv_content.encode("utf-8"), "text/csv")}
        )
        assert up_res.status_code == 201
        dataset_id = up_res.json()["id"]

        # 2. Verify deterministic profile
        prof_res = await ac.get(f"/datasets/{dataset_id}/profile")
        assert prof_res.status_code == 200
        assert "department" in prof_res.json()["schema_info"]

        # 3. Generate questions
        q_res = await ac.post(f"/datasets/{dataset_id}/questions")
        assert q_res.status_code == 201
        questions = q_res.json()
        assert len(questions) > 0
        target_question_id = questions[0]["id"]

        # 4. Trigger analysis run
        run_res = await ac.post("/runs", json={"question_id": target_question_id, "dataset_id": dataset_id})
        assert run_res.status_code == 202
        run_data = run_res.json()
        run_id = run_data["id"]
        assert run_data["status"] in ["success", "completed"]
        assert len(run_data["attempts"]) >= 1

        # 5. Verify grounded insight
        assert run_data["insight"] is not None
        assert len(run_data["insight"]["text"]) > 10

        # 6. Generate and verify report
        rep_res = await ac.post(f"/datasets/{dataset_id}/report")
        assert rep_res.status_code == 201
        report = rep_res.json()
        assert "# Dataset Analysis Report" in report["content"]
        assert "company_eda.csv" in report["content"]
        assert "## Findings" in report["content"]
