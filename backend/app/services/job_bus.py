import asyncio
import uuid
from typing import Dict, List, Any, Optional
from fastapi import WebSocket
import app.db.session as db_session
from app.db.repositories import DatasetRepository
from app.agents.graph import analysis_graph
from app.agents.state import AnalysisState

class JobBus:
    def __init__(self):
        # dataset_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, dataset_id: str, websocket: WebSocket):
        await websocket.accept()
        if dataset_id not in self.active_connections:
            self.active_connections[dataset_id] = []
        self.active_connections[dataset_id].append(websocket)

    def disconnect(self, dataset_id: str, websocket: WebSocket):
        if dataset_id in self.active_connections:
            if websocket in self.active_connections[dataset_id]:
                self.active_connections[dataset_id].remove(websocket)
            if not self.active_connections[dataset_id]:
                del self.active_connections[dataset_id]

    async def broadcast(self, dataset_id: str, message: Dict[str, Any]):
        if dataset_id in self.active_connections:
            websockets = list(self.active_connections[dataset_id])
            for ws in websockets:
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(dataset_id, ws)

    async def run_question_pipeline(self, question_id: str, dataset_id: str, run_id: Optional[str] = None) -> str:
        run_id = run_id or str(uuid.uuid4())
        
        async with db_session.AsyncSessionLocal() as session:
            repo = DatasetRepository(session)
            await repo.create_analysis_run(run_id, question_id)
            
            question = await repo.get_research_question(question_id)
            dataset = await repo.get_dataset(dataset_id)
            profile = await repo.get_profile(dataset_id)

        await self.broadcast(dataset_id, {
            "type": "run_started",
            "run_id": run_id,
            "question_id": question_id,
            "status": "Generating analysis code..."
        })

        initial_state: AnalysisState = {
            "dataset_id": dataset_id,
            "question_id": question_id,
            "run_id": run_id,
            "question": question.question,
            "columns_involved": question.columns_involved or [],
            "category": question.category or "exploratory",
            "schema_info": profile.schema_info or {},
            "profile_info": profile.numeric_stats or {},
            "dataset_path": dataset.stored_path,
            "file_type": dataset.file_type,
            "current_attempt": 0,
            "max_attempts": 3,
            "current_code": "",
            "execution_history": [],
            "last_exit_code": None,
            "last_stdout": None,
            "last_stderr": None,
            "last_duration_ms": None,
            "last_failure_type": None,
            "last_output_files": [],
            "parsed_findings": None,
            "insight": None,
            "visualization": None,
            "status": "started"
        }

        # Run LangGraph pipeline with streaming transitions
        final_state = dict(initial_state)
        async for output in analysis_graph.astream(initial_state):
            for node_name, node_output in output.items():
                if isinstance(node_output, dict):
                    final_state.update(node_output)

                transition_events = {
                    "code_generator": "code_generating",
                    "sandbox_execute": "sandbox_executing",
                    "code_corrector": "correction_started",
                    "result_analyzer": "analysis_success",
                    "insight_writer": "insight_generating",
                    "visualization_builder": "visualization_generating",
                    "failed_end": "failed"
                }
                event_name = transition_events.get(node_name, node_name)

                await self.broadcast(dataset_id, {
                    "type": "pipeline_transition",
                    "event": event_name,
                    "node": node_name,
                    "run_id": run_id,
                    "question_id": question_id,
                    "attempt": final_state.get("current_attempt", 1),
                    "status": final_state.get("status", "running")
                })

        # Persist results
        async with db_session.AsyncSessionLocal() as session:
            repo = DatasetRepository(session)
            await repo.save_run_results(run_id, final_state)

        await self.broadcast(dataset_id, {
            "type": "run_completed",
            "run_id": run_id,
            "question_id": question_id,
            "status": final_state.get("status"),
            "insight": final_state.get("insight"),
            "visualization": final_state.get("visualization")
        })

        return run_id

job_bus = JobBus()
