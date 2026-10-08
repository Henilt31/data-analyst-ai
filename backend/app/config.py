from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "DataMind"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/datamind",
        description="Database connection string"
    )
    
    # LLM settings
    LLM_PROVIDER: str = Field(default="openrouter", description="openrouter, gemini, or ollama")
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API Key")
    GOOGLE_API_KEY: str = Field(default="", description="Google Gemini API Key")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama Base URL")
    
    QUESTION_GENERATOR_MODEL: str = Field(default="google/gemini-2.5-flash", description="Model for generating questions")
    CODE_GENERATOR_MODEL: str = Field(default="google/gemini-2.5-flash", description="Model for generating analysis code")
    CODE_CORRECTOR_MODEL: str = Field(default="google/gemini-2.5-flash", description="Model for code self-correction")
    INSIGHT_WRITER_MODEL: str = Field(default="google/gemini-2.5-flash", description="Model for writing grounded insights")
    
    # Sandbox settings
    USE_DOCKER_SANDBOX: bool = Field(default=True, description="Whether to execute code in Docker sandbox")
    MAX_ATTEMPTS: int = Field(default=3, description="Maximum self-correction attempts")
    SANDBOX_TIMEOUT_SECONDS: int = Field(default=60, description="Execution timeout in seconds")
    SANDBOX_MEMORY_LIMIT: str = Field(default="512m", description="Docker memory limit")
    SANDBOX_CPU_LIMIT: float = Field(default=1.0, description="Docker CPU limit")
    SANDBOX_IMAGE: str = Field(default="datamind-sandbox:latest", description="Sandbox Docker image")
    
    # Storage paths
    RAG_PERSIST_DIR: str = str(BASE_DIR.parent / "data" / "rag")
    LOGS_DIR: str = str(BASE_DIR.parent / "data" / "logs")
    DATASET_DIR: str = str(BASE_DIR.parent / "data" / "datasets")
    OUTPUT_DIR: str = str(BASE_DIR.parent / "data" / "outputs")
    
    model_config = ConfigDict(env_file=".env", extra="allow")

settings = Settings()

# Ensure directories exist
os.makedirs(settings.RAG_PERSIST_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)
os.makedirs(settings.DATASET_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
