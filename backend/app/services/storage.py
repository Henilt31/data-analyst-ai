import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config import settings

ALLOWED_EXTENSIONS = {
    "csv": "text/csv",
    "json": "application/json",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "parquet": "application/octet-stream"
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB configurable limit

class StorageService:
    def __init__(self, upload_dir: str = settings.DATASET_DIR):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, filename: str, content_type: Optional[str] = None) -> str:
        if not filename or "." not in filename:
            raise HTTPException(status_code=400, detail="Invalid filename: must have an extension")
        
        ext = filename.rsplit(".", 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(ALLOWED_EXTENSIONS.keys())}"
            )
        return ext

    async def save_uploaded_file(self, file: UploadFile) -> tuple[str, str, int, str]:
        """
        Validates and saves the uploaded file safely with UUID to prevent path traversal.
        Returns: (dataset_id, stored_path, file_size, file_type)
        """
        ext = self.validate_file(file.filename, file.content_type)
        dataset_id = str(uuid.uuid4())
        safe_filename = f"{dataset_id}.{ext}"
        target_path = self.upload_dir / safe_filename

        total_bytes = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        async with aiofiles.open(target_path, "wb") as out_file:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    # Clean up
                    await out_file.close()
                    if target_path.exists():
                        target_path.unlink()
                    raise HTTPException(
                        status_code=413, 
                        detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
                    )
                await out_file.write(chunk)

        return dataset_id, str(target_path.resolve()), total_bytes, ext

storage_service = StorageService()
