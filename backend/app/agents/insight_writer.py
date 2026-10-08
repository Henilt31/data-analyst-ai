import json
from typing import Dict, Any
from pydantic import BaseModel
from app.agents.state import AnalysisState
from app.services.llm import llm_client
from app.config import settings

class GroundedInsightOutput(BaseModel):
    text: str
    evidence: Dict[str, Any]
    important_numbers: Dict[str, Any]
    caveats: str
    takeaway: str

async def insight_writer_node(state: AnalysisState) -> Dict[str, Any]:
    question = state["question"]
    findings = state.get("parsed_findings", {})
    stdout = state.get("last_stdout", "")

    system_prompt = (
        "You are an analytical reporting specialist adhering strictly to factual grounding.\n"
        "RULES FOR INSIGHTS:\n"
        "1. STRICT GROUNDING: You MUST NOT invent, guess, or approximate any numbers. Every metric or number cited "
        "must be derived directly from the computed execution results or stdout.\n"
        "2. Formulate a crisp, definitive answer to the user's research question based on the evidence.\n"
        "3. Explicitly state the evidence and numbers computed.\n"
        "4. Highlight any analytical caveats (e.g. sample size, variance, missing data).\n"
        "5. Conclude with a strategic takeaway."
    )

    prompt = f"""
Research Question: {question}

Computed Execution Results (GROUND TRUTH):
{json.dumps(findings, indent=2)}

Full Execution Output:
{stdout[:1500]}

Generate the grounded analytical insight. Return JSON matching:
{{
  "text": "Comprehensive grounded answer...",
  "evidence": {{"key_metric": 12.3}},
  "important_numbers": {{"metric": 12.3}},
  "caveats": "Caveats...",
  "takeaway": "Actionable conclusion..."
}}
"""

    insight_obj = await llm_client.generate_json(
        prompt, 
        GroundedInsightOutput, 
        system_prompt=system_prompt, 
        model=settings.INSIGHT_WRITER_MODEL
    )

    return {
        "insight": insight_obj.model_dump(),
        "status": "success"
    }
