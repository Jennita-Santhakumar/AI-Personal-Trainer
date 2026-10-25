"""
api/routers/coach.py — AI coach endpoints (Ollama / local LLM).
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json as _json
import traceback

from database import get_db
from models import User, WorkoutSession, CoachConversation, WorkoutPlan, PersonalRecord
from api.middleware.auth import get_current_user
from features.coach.coach import AICoach
from features.coach.memory import UserCoachProfile, WorkoutMemory
from config import get_settings

router   = APIRouter(prefix="/api/v1/coach", tags=["coach"])
settings = get_settings()


def _require_ollama():
    """Ollama is always available if the Docker service is up — no key needed."""
    if not settings.ollama_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama URL not configured. Set OLLAMA_URL in your .env (default: http://ollama:11434).",
        )


async def load_profile(user: User, db: AsyncSession) -> UserCoachProfile:
    from datetime import date as date_type

    # --- Sessions ---
    result = await db.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id)
        .order_by(WorkoutSession.created_at.desc())
        .limit(20)
    )
    sessions = result.scalars().all()
    history = [
        WorkoutMemory(
            session_id=s.id, date=s.created_at.date().isoformat(),
            activity=s.activity or "workout",
            form_violations=list(s.form_violations.keys()) if s.form_violations else [],
            quality_score=s.avg_quality, perceived_effort=s.perceived_effort,
            sets_completed=s.sets_completed or 0, notes=s.notes,
        )
        for s in sessions
    ]

    # --- Streak ---
    streak = 0
    prev_date = None
    for s in sessions:
        d = s.created_at.date()
        if prev_date is None or (prev_date - d).days == 1:
            streak += 1
        else:
            break
        prev_date = d

    # --- Program week: derive from the most recent active plan ---
    program_week = 1
    plan_result = await db.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user.id)
        .order_by(WorkoutPlan.created_at.desc())
        .limit(1)
    )
    latest_plan = plan_result.scalar_one_or_none()
    if latest_plan:
        days_since = (date_type.today() - latest_plan.created_at.date()).days
        program_week = max(1, (days_since // 7) + 1)

    # --- Personal records ---
    pr_result = await db.execute(
        select(PersonalRecord).where(PersonalRecord.user_id == user.id)
    )
    prs = {r.exercise: r.weight_kg for r in pr_result.scalars().all() if r.weight_kg}

    return UserCoachProfile(
        user_id=user.id,
        name=user.name or "Athlete",
        goal=user.goal or "general fitness",
        level=user.level or "intermediate",
        injuries=user.injuries or [],
        preferences=user.preferences or {},
        workout_history=history,
        consecutive_days_trained=streak,
        current_program_week=program_week,
        personal_records=prs,
    )


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/message")
async def coach_message(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Streams coach response as NDJSON so the client sees tokens immediately
    instead of waiting for the full reply.  Each line is a JSON object:
      {"chunk": "..."}   — incremental text
      {"done": true}     — signals end of stream
    The HTTP fallback in useCoach.js already handles plain-text chunks,
    so this is fully backward-compatible.
    """
    _require_ollama()

    try:
        profile = await load_profile(user, db)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Profile load error: {str(e)}")

    async def generate():
        coach = AICoach()
        full = ""
        try:
            async for chunk in coach.chat(req.message, profile, None):
                full += chunk
                yield _json.dumps({"chunk": chunk}) + "\n"
        except Exception as e:
            yield _json.dumps({"error": str(e)}) + "\n"
            return

        # Persist conversation after streaming completes
        try:
            for role, content in [("user", req.message), ("assistant", full)]:
                db.add(CoachConversation(
                    user_id=user.id, role=role, content=content,
                    session_id=req.session_id,
                ))
            await db.commit()
        except Exception as e:
            print(f"[coach] failed to persist conversation: {e}")

        yield _json.dumps({"done": True}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.websocket("/stream")
async def coach_stream(websocket: WebSocket, token: str, db: AsyncSession = Depends(get_db)):
    from jose import jwt
    await websocket.accept()
    if not settings.ollama_url:
        await websocket.send_json({"error": "Ollama not configured — set OLLAMA_URL in .env"})
        await websocket.close(code=1011)
        return
    try:
        payload  = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id  = payload.get("sub")
        result   = await db.execute(select(User).where(User.id == user_id))
        user     = result.scalar_one_or_none()
        if not user:
            await websocket.close(code=4001); return
        coach   = AICoach()
        profile = await load_profile(user, db)
        while True:
            data    = await websocket.receive_json()
            message = data.get("message", "")
            async for chunk in coach.chat(message, profile, None):
                await websocket.send_text(chunk)
            await websocket.send_json({"done": True})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try: await websocket.send_json({"error": str(e)})
        except: pass
        await websocket.close(code=1011)


@router.get("/briefing")
async def daily_briefing(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_ollama()
    try:
        profile  = await load_profile(user, db)
        coach    = AICoach()
        briefing = await coach.daily_briefing_async(profile)
        return {"briefing": briefing, "generated_at": datetime.utcnow().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Briefing error: {str(e)}")


@router.get("/history")
async def conversation_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CoachConversation)
        .where(CoachConversation.user_id == user.id)
        .order_by(CoachConversation.created_at.desc())
        .limit(limit)
    )
    convs = result.scalars().all()
    return [{"role": c.role, "content": c.content,
             "created_at": c.created_at.isoformat()} for c in reversed(convs)]
