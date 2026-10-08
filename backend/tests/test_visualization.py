import pytest
from app.agents.visualization_builder import visualization_builder_node
from app.agents.state import AnalysisState

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_visualization_builder_detects_chart_file(tmp_path):
    chart_file = tmp_path / "chart.png"
    chart_file.write_bytes(b"\x89PNG\r\n\x1a\n")

    state: AnalysisState = {
        "question": "What is the distribution of transaction values?",
        "category": "distribution",
        "last_output_files": [str(chart_file)],
        "parsed_findings": {"mean": 120.5, "median": 95.0}
    } # type: ignore

    result = await visualization_builder_node(state)
    assert result["visualization"] is not None
    viz = result["visualization"]
    assert viz["chart_type"] == "histogram"
    assert viz["chart_path"] == str(chart_file)
    assert "distribution" in viz["title"].lower()

@pytest.mark.anyio
async def test_visualization_builder_handles_no_chart():
    state: AnalysisState = {
        "question": "Count of records",
        "category": "exploratory",
        "last_output_files": ["outputs/results.txt"],
        "parsed_findings": {"count": 500}
    } # type: ignore

    result = await visualization_builder_node(state)
    assert result["visualization"] is None
