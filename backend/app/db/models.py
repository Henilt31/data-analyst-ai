from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=utc_now)

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    status = Column(String, default="uploaded")
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    
    profile = relationship("DatasetProfile", back_populates="dataset", uselist=False, cascade="all, delete-orphan")
    questions = relationship("ResearchQuestion", back_populates="dataset", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="dataset", uselist=False, cascade="all, delete-orphan")

class DatasetProfile(Base):
    __tablename__ = "dataset_profiles"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    schema_info = Column(JSON, nullable=True)
    missing_data = Column(JSON, nullable=True)
    numeric_stats = Column(JSON, nullable=True)
    categorical_stats = Column(JSON, nullable=True)
    datetime_stats = Column(JSON, nullable=True)
    data_quality = Column(JSON, nullable=True)
    correlations = Column(JSON, nullable=True)
    
    dataset = relationship("Dataset", back_populates="profile")

class ResearchQuestion(Base):
    __tablename__ = "research_questions"
    
    id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    question = Column(String, nullable=False)
    rationale = Column(Text, nullable=True)
    columns_involved = Column(JSON, nullable=True)
    category = Column(String, nullable=True)
    
    dataset = relationship("Dataset", back_populates="questions")
    runs = relationship("AnalysisRun", back_populates="question", cascade="all, delete-orphan")

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    
    id = Column(String, primary_key=True, index=True)
    question_id = Column(String, ForeignKey("research_questions.id"))
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=utc_now)
    
    question = relationship("ResearchQuestion", back_populates="runs")
    attempts = relationship("AnalysisAttempt", back_populates="run", cascade="all, delete-orphan")
    insight = relationship("Insight", back_populates="run", uselist=False, cascade="all, delete-orphan")
    visualization = relationship("Visualization", back_populates="run", uselist=False, cascade="all, delete-orphan")

class AnalysisAttempt(Base):
    __tablename__ = "analysis_attempts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String, ForeignKey("analysis_runs.id"))
    attempt_number = Column(Integer, nullable=False)
    generated_code = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String, nullable=False)
    failure_type = Column(String, nullable=True)
    
    run = relationship("AnalysisRun", back_populates="attempts")

class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String, ForeignKey("analysis_runs.id"))
    text = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)
    important_numbers = Column(JSON, nullable=True)
    caveats = Column(Text, nullable=True)
    takeaway = Column(Text, nullable=True)
    
    run = relationship("AnalysisRun", back_populates="insight")

class Visualization(Base):
    __tablename__ = "visualizations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String, ForeignKey("analysis_runs.id"))
    chart_type = Column(String, nullable=False)
    chart_path = Column(String, nullable=False)
    title = Column(String, nullable=True)
    data = Column(JSON, nullable=True)
    
    run = relationship("AnalysisRun", back_populates="visualization")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    dataset = relationship("Dataset", back_populates="report")

class TelemetryTrial(Base):
    __tablename__ = "telemetry_trials"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(String, nullable=True, index=True)
    question_id = Column(String, nullable=True, index=True)
    run_id = Column(String, nullable=True, index=True)
    attempt_number = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    failure_type = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    llm_model = Column(String, nullable=True)
    token_usage = Column(JSON, nullable=True)
    llm_call_count = Column(Integer, default=1)
    rag_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
