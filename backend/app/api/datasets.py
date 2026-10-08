from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
import app.db.session as db_session
from app.db.repositories import DatasetRepository
from app.services.storage import storage_service
from app.services.profiling import profiling_service
from app.schemas.dataset import DatasetResponse, DatasetProfileResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])

async def run_profiling_task(dataset_id: str, stored_path: str, file_type: str):
    async with db_session.AsyncSessionLocal() as session:
        repo = DatasetRepository(session)
        try:
            profile_data = profiling_service.profile_file(stored_path, file_type)
            await repo.save_profile(dataset_id, profile_data)
        except Exception as e:
            await repo.update_dataset_status(dataset_id, status=f"profiling_failed: {str(e)[:50]}")

@router.post("", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    dataset_id, stored_path, file_size, file_type = await storage_service.save_uploaded_file(file)
    
    repo = DatasetRepository(db)
    dataset = await repo.create_dataset(
        id=dataset_id,
        original_filename=file.filename or f"dataset.{file_type}",
        stored_path=stored_path,
        file_type=file_type,
        file_size=file_size
    )

    # Deterministically profile the dataset immediately (or in background)
    # To ensure profiling is immediately available for the user/test, we run it or schedule it
    profile_data = profiling_service.profile_file(stored_path, file_type)
    await repo.save_profile(dataset_id, profile_data)

    # Refresh dataset to return updated row/col count and status
    refreshed_dataset = await repo.get_dataset(dataset_id)
    return refreshed_dataset or dataset

@router.get("", response_model=List[DatasetResponse])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    repo = DatasetRepository(db)
    return await repo.list_datasets()

@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    repo = DatasetRepository(db)
    dataset = await repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@router.get("/{dataset_id}/profile", response_model=DatasetProfileResponse)
async def get_dataset_profile(dataset_id: str, db: AsyncSession = Depends(get_db)):
    repo = DatasetRepository(db)
    dataset = await repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    profile = await repo.get_profile(dataset_id)
    if not profile:
        # If not profiled yet, run profiling now
        profile_data = profiling_service.profile_file(dataset.stored_path, dataset.file_type)
        profile = await repo.save_profile(dataset_id, profile_data)
    return profile
