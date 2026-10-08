from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from app.agents.state import AnalysisState
from app.agents.code_generator import generate_code_node
from app.agents.code_corrector import correct_code_node
from app.agents.result_analyzer import result_analyzer_node
from app.agents.insight_writer import insight_writer_node
from app.agents.visualization_builder import visualization_builder_node
from app.services.sandbox import sandbox_service
from app.services.telemetry import telemetry_service

async def sandbox_execute_node(state: AnalysisState) -> Dict[str, Any]:
    code = state["current_code"]
    dataset_path = state["dataset_path"]
    run_id = state["run_id"]
    attempt = state.get("current_attempt", 0) + 1

    exec_result = sandbox_service.execute_code(
        code=code,
        dataset_path=dataset_path,
        run_id=run_id,
        attempt=attempt
    )

    attempt_record = {
        "attempt_number": attempt,
        "generated_code": code,
        "exit_code": exec_result.exit_code,
        "stdout": exec_result.stdout,
        "stderr": exec_result.stderr,
        "duration_ms": exec_result.duration_ms,
        "status": "success" if exec_result.is_success else "failed",
        "failure_type": exec_result.failure_type
    }

    # Log telemetry
    telemetry_service.log_trial(
        dataset_id=state["dataset_id"],
        question_id=state["question_id"],
        run_id=run_id,
        attempt=attempt,
        status="success" if exec_result.is_success else "failed",
        failure_type=exec_result.failure_type,
        duration_ms=exec_result.duration_ms
    )

    history = list(state.get("execution_history", []))
    history.append(attempt_record)

    return {
        "current_attempt": attempt,
        "last_exit_code": exec_result.exit_code,
        "last_stdout": exec_result.stdout,
        "last_stderr": exec_result.stderr,
        "last_duration_ms": exec_result.duration_ms,
        "last_failure_type": exec_result.failure_type,
        "last_output_files": exec_result.output_files,
        "execution_history": history,
        "status": "success" if exec_result.is_success else "failed"
    }

def check_execution_success(state: AnalysisState) -> Literal["result_analyzer", "code_corrector", "failed_end"]:
    if state["status"] == "success":
        return "result_analyzer"
    
    if state["current_attempt"] < state.get("max_attempts", 3):
        return "code_corrector"
    
    return "failed_end"

async def failed_end_node(state: AnalysisState) -> Dict[str, Any]:
    return {"status": "failed"}

def create_analysis_graph() -> StateGraph:
    workflow = StateGraph(AnalysisState)

    # Add Nodes
    workflow.add_node("code_generator", generate_code_node)
    workflow.add_node("sandbox_execute", sandbox_execute_node)
    workflow.add_node("code_corrector", correct_code_node)
    workflow.add_node("result_analyzer", result_analyzer_node)
    workflow.add_node("insight_writer", insight_writer_node)
    workflow.add_node("visualization_builder", visualization_builder_node)
    workflow.add_node("failed_end", failed_end_node)

    # Set Entry Point
    workflow.set_entry_point("code_generator")

    # Add Edges
    workflow.add_edge("code_generator", "sandbox_execute")

    # Conditional Branching after Execution
    workflow.add_conditional_edges(
        "sandbox_execute",
        check_execution_success,
        {
            "result_analyzer": "result_analyzer",
            "code_corrector": "code_corrector",
            "failed_end": "failed_end"
        }
    )

    # Self-Correction Loop: corrector returns to sandbox
    workflow.add_edge("code_corrector", "sandbox_execute")

    # Success Path
    workflow.add_edge("result_analyzer", "insight_writer")
    workflow.add_edge("insight_writer", "visualization_builder")
    workflow.add_edge("visualization_builder", END)
    workflow.add_edge("failed_end", END)

    return workflow.compile()

analysis_graph = create_analysis_graph()
