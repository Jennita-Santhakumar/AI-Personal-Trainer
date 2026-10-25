"""
api/routers/auth.py — registration, login, token refresh.

Fixes:
  - Removed the brittle __import__() hack on /me endpoint; imported properly.
  - get_me now correctly injects get_current_user via Depends.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from database import get_db
from models import User, GamificationState
from api.middleware.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    goal: str = "strength"
    level: str = "beginner"
    age: int = 25
    weight_kg: float = 70.0
    height_cm: float = 170.0


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        name=req.name,
        goal=req.goal,
        level=req.level,
        age=req.age,
        weight_kg=req.weight_kg,
        height_cm=req.height_cm,
        injuries=[],
        preferences={},
    )
    db.add(user)
    await db.flush()

    # Create default gamification state
    gam = GamificationState(user_id=user.id, badges_earned=[], activities_tried=[])
    db.add(gam)
    await db.commit()

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user_id=user.id, name=user.name or "")


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user_id=user.id, name=user.name or "")


# FIX: replaced __import__() hack with a proper import at module level
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "goal": current_user.goal,
        "level": current_user.level,
        "injuries": current_user.injuries or [],
        "weight_kg": current_user.weight_kg,
        "height_cm": current_user.height_cm,
    }
