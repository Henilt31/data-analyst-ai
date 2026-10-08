from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime

class DatasetBase(BaseModel):
    original_filename: str
    file_type: str
    file_size: int

class DatasetCreate(DatasetBase):
    id: str
    stored_path: str

class DatasetResponse(DatasetBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    stored_path: str
    status: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    created_at: datetime

class DatasetProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    dataset_id: str
    schema_info: Optional[Dict[str, Any]] = None
    missing_data: Optional[Dict[str, Any]] = None
    numeric_stats: Optional[Dict[str, Any]] = None
    categorical_stats: Optional[Dict[str, Any]] = None
    datetime_stats: Optional[Dict[str, Any]] = None
    data_quality: Optional[Dict[str, Any]] = None
    correlations: Optional[Dict[str, Any]] = None
