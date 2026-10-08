import hashlib
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

class AuthRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    stmt = select(User).where(User.username == req.username)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_id = str(uuid.uuid4())
    new_user = User(
        id=user_id,
        username=req.username,
        hashed_password=hash_password(req.password),
        created_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(new_user)
    await db.commit()

    token = f"token_{user_id}_{hash_password(req.password)[:16]}"
    return AuthResponse(access_token=token, user_id=user_id, username=req.username)

@router.post("/login", response_model=AuthResponse)
async def login(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == req.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or user.hashed_password != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = f"token_{user.id}_{user.hashed_password[:16]}"
    return AuthResponse(access_token=token, user_id=user.id, username=user.username)
