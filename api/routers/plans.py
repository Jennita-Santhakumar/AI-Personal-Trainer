"""
api/routers/plans.py — workout plan generation and retrieval endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from database import get_db
from models import User, WorkoutPlan
from api.middleware.auth import get_current_user
from features.workout_split.generator import (
    WorkoutSplitGenerator, UserProfile, Goal, Level
)

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])


class GeneratePlanRequest(BaseModel):
    goal: str = Field(..., pattern="^(strength|fat_loss|endurance|flexibility|hybrid)$")
    level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    days_per_week: int = Field(..., ge=2, le=6)
    injuries: List[str] = []
    sport_focus: str = "general"
    current_maxes: Dict[str, float] = {}
    weeks: int = Field(default=4, ge=1, le=12)


@router.post("/generate", status_code=201)
async def generate_plan(
    req: GeneratePlanRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a personalised multi-week workout split and persist it."""
    profile = UserProfile(
        goal=Goal(req.goal),
        level=Level(req.level),
        days_per_week=req.days_per_week,
        injuries=req.injuries,
        sport_focus=req.sport_focus,
        current_maxes=req.current_maxes,
        weight_kg=user.weight_kg or 70.0,
        age=user.age or 25,
    )
    generator = WorkoutSplitGenerator()
    splits = generator.generate(profile, weeks=req.weeks)

    # Deactivate previous plans
    await db.execute(
        update(WorkoutPlan)
        .where(WorkoutPlan.user_id == user.id, WorkoutPlan.active == True)
        .values(active=False)
    )

    plan = WorkoutPlan(
        id=str(uuid.uuid4()),
        user_id=user.id,
        goal=req.goal,
        level=req.level,
        weeks=req.weeks,
        plan_json=[s.to_dict() for s in splits],
        active=True,
    )
    db.add(plan)
    await db.commit()

    return {"plan_id": plan.id, "weeks": plan.plan_json}


@router.get("/current")
async def get_current_plan(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user.id, WorkoutPlan.active == True)
        .order_by(WorkoutPlan.created_at.desc())
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="No active plan found. Generate one first.")
    return {"plan_id": plan.id, "goal": plan.goal, "level": plan.level,
            "weeks": plan.weeks, "plan": plan.plan_json, "created_at": plan.created_at.isoformat()}


@router.get("/history")
async def plan_history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user.id)
        .order_by(WorkoutPlan.created_at.desc())
        .limit(10)
    )
    plans = result.scalars().all()
    return [{"plan_id": p.id, "goal": p.goal, "level": p.level,
             "active": p.active, "created_at": p.created_at.isoformat()} for p in plans]
