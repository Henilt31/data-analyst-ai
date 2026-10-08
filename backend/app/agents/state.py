from typing import TypedDict, List, Dict, Any, Optional

class AnalysisState(TypedDict):
    dataset_id: str
    question_id: str
    run_id: str
    question: str
    columns_involved: List[str]
    category: Optional[str]
    schema_info: Dict[str, Any]
    profile_info: Dict[str, Any]
    dataset_path: str
    file_type: str
    current_attempt: int
    max_attempts: int
    current_code: str
    execution_history: List[Dict[str, Any]]
    last_exit_code: Optional[int]
    last_stdout: Optional[str]
    last_stderr: Optional[str]
    last_duration_ms: Optional[int]
    last_failure_type: Optional[str]
    last_output_files: List[str]
    parsed_findings: Optional[Dict[str, Any]]
    insight: Optional[Dict[str, Any]]
    visualization: Optional[Dict[str, Any]]
    status: str
