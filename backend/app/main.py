from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Database schema auto-init note: {e}")
    yield

app = FastAPI(title="DataMind API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.auth import router as auth_router
from app.api.datasets import router as datasets_router
from app.api.questions import router as questions_router
from app.api.runs import router as runs_router
from app.api.reports import router as reports_router

app.include_router(auth_router)
app.include_router(datasets_router)
app.include_router(questions_router)
app.include_router(runs_router)
app.include_router(reports_router)



@app.get("/health")
async def health_check():
    return {"status": "ok"}

