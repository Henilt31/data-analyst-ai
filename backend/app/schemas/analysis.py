from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class QuestionItem(BaseModel):
    question: str
    rationale: Optional[str] = None
    columns: List[str] = []
    category: Optional[str] = None

class GeneratedQuestions(BaseModel):
    questions: List[QuestionItem]

class ResearchQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    dataset_id: str
    question: str
    rationale: Optional[str] = None
    columns_involved: Optional[List[str]] = None
    category: Optional[str] = None

class AnalysisAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    attempt_number: int
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    duration_ms: Optional[int] = None
    status: str
    failure_type: Optional[str] = None

class InsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    run_id: str
    text: str
    evidence: Optional[Any] = None
    important_numbers: Optional[Any] = None
    caveats: Optional[str] = None
    takeaway: Optional[str] = None

class VisualizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    run_id: str
    chart_type: str
    chart_path: str
    title: Optional[str] = None
    data: Optional[Any] = None

class AnalysisRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    question_id: str
    status: str
    created_at: datetime
    attempts: List[AnalysisAttemptResponse] = []
    insight: Optional[InsightResponse] = None
    visualization: Optional[VisualizationResponse] = None

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    dataset_id: str
    content: str
    created_at: datetime
