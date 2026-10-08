from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.session import get_db
from app.db.repositories import DatasetRepository
from app.services.job_bus import job_bus
from app.schemas.analysis import AnalysisRunResponse, InsightResponse

router = APIRouter(tags=["runs"])

class CreateRunRequest(BaseModel):
    question_id: str
    dataset_id: str

@router.post("/runs", response_model=AnalysisRunResponse, status_code=202)
async def trigger_analysis_run(
    req: CreateRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    repo = DatasetRepository(db)
    question = await repo.get_research_question(req.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Research question not found")

    import uuid
    run_id = str(uuid.uuid4())
    
    # Run the pipeline synchronously or via background task
    # To return full populated response immediately or track via WebSocket
    await job_bus.run_question_pipeline(req.question_id, req.dataset_id, run_id=run_id)
    
    run = await repo.get_run(run_id)
    return run

@router.get("/runs/{run_id}", response_model=AnalysisRunResponse)
async def get_analysis_run(run_id: str, db: AsyncSession = Depends(get_db)):
    repo = DatasetRepository(db)
    run = await repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return run

@router.get("/insights/{id}", response_model=InsightResponse)
async def get_insight(id: str, db: AsyncSession = Depends(get_db)):
    repo = DatasetRepository(db)
    insight = await repo.get_insight(id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    return insight

@router.websocket("/ws/datasets/{dataset_id}/status")
async def websocket_status_endpoint(websocket: WebSocket, dataset_id: str):
    await job_bus.connect(dataset_id, websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        job_bus.disconnect(dataset_id, websocket)
