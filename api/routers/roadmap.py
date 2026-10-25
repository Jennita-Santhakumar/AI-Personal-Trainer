"""
api/routers/roadmap.py — FastAPI endpoints for multi-week fitness & nutrition roadmap generation.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database import get_db
from models import User, FitnessRoadmap
from api.middleware.auth import get_current_user
from features.roadmap.schemas import (
    RoadmapRequest,
    RoadmapProgressUpdate,
    FitnessRoadmapData,
)
from features.roadmap.generator import FitnessRoadmapGenerator
from config import get_settings

router = APIRouter(prefix="/api/v1/roadmap", tags=["roadmap"])
settings = get_settings()


@router.get("/providers")
async def get_providers_status(user: User = Depends(get_current_user)):
    """Returns AI provider availability for the frontend."""
    return {
        "gemini": {
            "available": bool(getattr(settings, "gemini_api_key", "")),
            "model": getattr(settings, "gemini_model", "gemini-1.5-flash")
        },
        "groq": {
            "available": bool(getattr(settings, "groq_api_key", "")),
            "model": getattr(settings, "groq_model", "llama-3.3-70b-versatile")
        },
        "ollama": {
            "available": bool(getattr(settings, "ollama_url", "")),
            "url": getattr(settings, "ollama_url", "http://ollama:11434"),
            "model": getattr(settings, "coach_model", "llama3.1:8b")
        },
        "default": getattr(settings, "ai_provider", "auto")
    }


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_roadmap(
    req: RoadmapRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Generates a personalized multi-week workout and nutrition roadmap via LLM (or fallback engine),
    deactivates existing active roadmaps, and persists the new roadmap.
    """
    user_profile = {
        "user_id": user.id,
        "name": user.name or "Athlete",
        "age": user.age or 26,
        "weight_kg": user.weight_kg or 75.0,
        "height_cm": user.height_cm or 178.0,
        "goal": req.goal,
        "level": req.level,
        "injuries": req.injuries or user.injuries or [],
    }

    generator = FitnessRoadmapGenerator()
    try:
        roadmap_data, provider_used = await generator.generate(req, user_profile)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate roadmap: {str(e)}"
        )

    # Deactivate previous active roadmaps
    await db.execute(
        update(FitnessRoadmap)
        .where(FitnessRoadmap.user_id == user.id, FitnessRoadmap.active == True)
        .values(active=False)
    )

    roadmap_dict = roadmap_data.model_dump()
    roadmap_record = FitnessRoadmap(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title=roadmap_data.title,
        goal=req.goal,
        level=req.level,
        duration_weeks=req.weeks,
        days_per_week=req.days_per_week,
        roadmap_data=roadmap_dict,
        progress_data={},
        provider_used=provider_used,
        active=True,
    )
    db.add(roadmap_record)
    await db.commit()
    await db.refresh(roadmap_record)

    return {
        "id": roadmap_record.id,
        "title": roadmap_record.title,
        "goal": roadmap_record.goal,
        "level": roadmap_record.level,
        "duration_weeks": roadmap_record.duration_weeks,
        "days_per_week": roadmap_record.days_per_week,
        "provider_used": roadmap_record.provider_used,
        "roadmap": roadmap_record.roadmap_data,
        "progress": roadmap_record.progress_data,
        "created_at": roadmap_record.created_at.isoformat(),
        "active": roadmap_record.active,
    }


@router.get("/current")
async def get_current_roadmap(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retrieves the active roadmap for the authenticated user."""
    result = await db.execute(
        select(FitnessRoadmap)
        .where(FitnessRoadmap.user_id == user.id, FitnessRoadmap.active == True)
        .order_by(FitnessRoadmap.created_at.desc())
    )
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active roadmap found. Please generate one first."
        )

    return {
        "id": roadmap.id,
        "title": roadmap.title,
        "goal": roadmap.goal,
        "level": roadmap.level,
        "duration_weeks": roadmap.duration_weeks,
        "days_per_week": roadmap.days_per_week,
        "provider_used": roadmap.provider_used,
        "roadmap": roadmap.roadmap_data,
        "progress": roadmap.progress_data or {},
        "created_at": roadmap.created_at.isoformat(),
        "active": roadmap.active,
    }


@router.get("/history")
async def get_roadmap_history(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lists all generated roadmaps for the user."""
    result = await db.execute(
        select(FitnessRoadmap)
        .where(FitnessRoadmap.user_id == user.id)
        .order_by(FitnessRoadmap.created_at.desc())
        .limit(15)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "goal": r.goal,
            "level": r.level,
            "duration_weeks": r.duration_weeks,
            "days_per_week": r.days_per_week,
            "provider_used": r.provider_used,
            "active": r.active,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@router.post("/{roadmap_id}/progress")
async def update_roadmap_progress(
    roadmap_id: str,
    update_req: RoadmapProgressUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Toggles completion state for an exercise, meal, or milestone in the roadmap."""
    result = await db.execute(
        select(FitnessRoadmap).where(
            FitnessRoadmap.id == roadmap_id,
            FitnessRoadmap.user_id == user.id
        )
    )
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")

    progress = dict(roadmap.progress_data or {})
    if update_req.completed:
        progress[update_req.task_id] = True
    else:
        progress.pop(update_req.task_id, None)

    roadmap.progress_data = progress
    await db.commit()

    return {"status": "ok", "progress": roadmap.progress_data}


@router.put("/{roadmap_id}/activate")
async def activate_roadmap(
    roadmap_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Switches active roadmap to a past one."""
    await db.execute(
        update(FitnessRoadmap)
        .where(FitnessRoadmap.user_id == user.id)
        .values(active=False)
    )
    await db.execute(
        update(FitnessRoadmap)
        .where(FitnessRoadmap.id == roadmap_id, FitnessRoadmap.user_id == user.id)
        .values(active=True)
    )
    await db.commit()
    return {"status": "ok", "active_roadmap_id": roadmap_id}


@router.delete("/{roadmap_id}")
async def delete_roadmap(
    roadmap_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Deletes a roadmap record."""
    await db.execute(
        delete(FitnessRoadmap).where(
            FitnessRoadmap.id == roadmap_id,
            FitnessRoadmap.user_id == user.id
        )
    )
    await db.commit()
    return {"status": "ok", "deleted_id": roadmap_id}
