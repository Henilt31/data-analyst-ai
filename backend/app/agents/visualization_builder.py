import os
from pathlib import Path
from typing import Dict, Any, Optional
from app.agents.state import AnalysisState

async def visualization_builder_node(state: AnalysisState) -> Dict[str, Any]:
    output_files = state.get("last_output_files", [])
    question = state["question"]
    findings = state.get("parsed_findings", {})
    category = state.get("category", "")

    # Check if an image file was generated in output files
    chart_path = None
    for f in output_files:
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".svg")):
            chart_path = f
            break

    if not chart_path:
        return {"visualization": None}

    # Determine chart type based on category or findings
    chart_type = "bar"
    if "distribution" in category.lower():
        chart_type = "histogram"
    elif "trend" in category.lower() or "temporal" in category.lower():
        chart_type = "line"
    elif "correlation" in category.lower():
        chart_type = "scatter"
    elif "segment" in category.lower():
        chart_type = "categorical comparison"

    title = f"Analysis: {question[:60]}"

    visualization = {
        "chart_type": chart_type,
        "chart_path": chart_path,
        "title": title,
        "data": findings
    }

    return {
        "visualization": visualization
    }
