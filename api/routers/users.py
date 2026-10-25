"""
api/routers/users.py — user profile management endpoints.

Fix: GamificationState has no .level column — it is computed from .points.
     Replaced gam.level with the correct level computation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from database import get_db
from models import User, WorkoutSession, PersonalRecord, GamificationState
from api.middleware.auth import get_current_user
from features.gamification.engine import LEVEL_THRESHOLDS

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _compute_level(points: int) -> str:
    level = "Beginner"
    for threshold, name in LEVEL_THRESHOLDS:
        if points >= threshold:
            level = name
    return level


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    goal: Optional[str] = None
    level: Optional[str] = None
    sport_focus: Optional[str] = None
    injuries: Optional[List[str]] = None
    preferences: Optional[Dict[str, str]] = None


@router.patch("/me")
async def update_profile(
    req: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await db.commit()
    return {"status": "updated", "user_id": user.id}


@router.get("/me/stats")
async def user_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Full user stats snapshot for profile page."""
    # Session counts
    total_r = await db.execute(
        select(func.count()).select_from(WorkoutSession).where(WorkoutSession.user_id == user.id)
    )
    total_sessions = total_r.scalar() or 0

    # Last 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)
    recent_r = await db.execute(
        select(func.count()).select_from(WorkoutSession).where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.created_at >= cutoff,
        )
    )
    recent_sessions = recent_r.scalar() or 0

    # PRs
    pr_r = await db.execute(
        select(PersonalRecord).where(PersonalRecord.user_id == user.id)
    )
    prs = {p.lift_name: p.value for p in pr_r.scalars().all()}

    # Gam
    gam_r = await db.execute(
        select(GamificationState).where(GamificationState.user_id == user.id)
    )
    gam = gam_r.scalar_one_or_none()

    return {
        "profile": {
            "name": user.name, "age": user.age, "goal": user.goal,
            "level": user.level, "weight_kg": user.weight_kg, "height_cm": user.height_cm,
            "injuries": user.injuries or [], "sport_focus": user.sport_focus,
        },
        "stats": {
            "total_sessions": total_sessions,
            "sessions_last_30_days": recent_sessions,
            "personal_records": prs,
        },
        "gamification": {
            "points": gam.points if gam else 0,
            "streak": gam.streak if gam else 0,
            # FIX: GamificationState has no .level column; compute from points
            "level": _compute_level(gam.points) if gam else "Beginner",
            "badges_earned": len(gam.badges_earned) if gam else 0,
        },
    }
