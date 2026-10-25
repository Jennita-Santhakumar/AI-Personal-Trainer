"""
api/routers/sessions.py — workout session logging and metrics.

FIXES:
  - datetime.fromisoformat() crashes on 'Z' suffix (JavaScript sends ISO strings with Z).
    Now strips Z and handles it properly.
  - BackgroundTasks with async functions: wrapped correctly.
  - Added GET / endpoint for session history (used by dashboard chart).
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio, uuid

from database import get_db
from models import User, WorkoutSession, GamificationState, PersonalRecord
from api.middleware.auth import get_current_user
from features.gamification.engine import GamificationEngine, GamificationStateData, InjuryRiskAnalyzer

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
gam_engine   = GamificationEngine()
risk_analyzer = InjuryRiskAnalyzer()


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string — handles both Z-suffix and +00:00."""
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00").replace("+00:00", ""))


class SubmitSessionRequest(BaseModel):
    activity: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    rep_count: int = 0
    avg_quality: Optional[float] = None
    perceived_effort: Optional[int] = None
    form_violations: Dict[str, int] = {}
    metrics: Dict = {}
    snapshots: List[dict] = []
    sets_completed: int = 0
    sleep_hours: Optional[float] = None
    notes: str = ""
    new_prs: Dict[str, float] = {}


@router.post("/", status_code=201)
async def submit_session(
    req: SubmitSessionRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session_id = str(uuid.uuid4())
    session = WorkoutSession(
        id=session_id,
        user_id=user.id,
        activity=req.activity,
        started_at=_parse_dt(req.started_at),
        ended_at=_parse_dt(req.ended_at),
        rep_count=req.rep_count,
        avg_quality=req.avg_quality,
        perceived_effort=req.perceived_effort,
        form_violations=req.form_violations or {},
        metrics=req.metrics or {},
        snapshots=req.snapshots or [],
        sets_completed=req.sets_completed,
        sleep_hours=req.sleep_hours,
        notes=req.notes,
    )
    db.add(session)
    for lift, value in (req.new_prs or {}).items():
        db.add(PersonalRecord(user_id=user.id, lift_name=lift, value=value, session_id=session_id))
    await db.commit()

    # Background gamification update — use sync wrapper so BackgroundTasks works reliably
    background.add_task(_run_gamification_sync, user.id, req, session_id)
    return {"session_id": session_id, "status": "saved"}


def _run_gamification_sync(user_id: str, req: SubmitSessionRequest, session_id: str):
    """Sync wrapper — BackgroundTasks runs this in a thread pool."""
    asyncio.run(_update_gamification(user_id, req, session_id))


async def _update_gamification(user_id: str, req: SubmitSessionRequest, session_id: str):
    from database import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(GamificationState).where(GamificationState.user_id == user_id))
            gam_row = result.scalar_one_or_none()
            if not gam_row:
                return
            state = GamificationStateData(
                user_id=user_id,
                points=gam_row.points,
                streak=gam_row.streak,
                longest_streak=gam_row.longest_streak,
                session_count=gam_row.session_count,
                consecutive_good_form=gam_row.consecutive_good_form,
                badges_earned=gam_row.badges_earned or [],
                activities_tried=gam_row.activities_tried or [],
                last_session_date=gam_row.last_session_date,
            )
            run_dist = req.metrics.get("distance_km") if req.activity in ("running", "easy_run") else None
            run_time = req.metrics.get("duration_minutes") if req.activity in ("running", "easy_run") else None
            updated, _ = gam_engine.process_session(
                state, req.activity, req.avg_quality, req.new_prs or None,
                run_distance_km=run_dist, run_time_minutes=run_time,
            )
            gam_row.points = updated.points
            gam_row.streak = updated.streak
            gam_row.longest_streak = updated.longest_streak
            gam_row.session_count = updated.session_count
            gam_row.consecutive_good_form = updated.consecutive_good_form
            gam_row.badges_earned = updated.badges_earned
            gam_row.activities_tried = updated.activities_tried
            gam_row.last_session_date = updated.last_session_date
            await db.commit()
    except Exception as e:
        print(f"[gamification] background update failed: {e}")


@router.get("/")
async def list_sessions(
    limit: int = 60,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id)
        .order_by(WorkoutSession.created_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id, "activity": s.activity,
            "sets_completed": s.sets_completed,
            "avg_quality": s.avg_quality,
            "perceived_effort": s.perceived_effort,
            "sleep_hours": s.sleep_hours,
            "notes": s.notes,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/summary")
async def metrics_summary(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id, WorkoutSession.created_at >= cutoff)
        .order_by(WorkoutSession.created_at.desc())
    )
    sessions = result.scalars().all()
    activities: Dict[str, int] = {}
    total_cals = 0.0; total_reps = 0; quality_scores = []
    for s in sessions:
        activities[s.activity] = activities.get(s.activity, 0) + 1
        if s.metrics: total_cals += s.metrics.get("calories", 0) or 0
        total_reps += s.rep_count or 0
        if s.avg_quality: quality_scores.append(s.avg_quality)
    return {
        "period_days": days, "total_sessions": len(sessions),
        "total_calories": round(total_cals), "total_reps": total_reps,
        "avg_quality": round(sum(quality_scores)/len(quality_scores), 3) if quality_scores else None,
        "avg_sessions_per_week": round(len(sessions)/(days/7), 1),
        "activity_breakdown": activities,
    }


@router.get("/injury-risk")
async def injury_risk(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == user.id)
        .order_by(WorkoutSession.created_at.desc())
        .limit(14)
    )
    sessions = result.scalars().all()
    history = [
        {"sets_completed": s.sets_completed, "perceived_effort": s.perceived_effort,
         "form_violations": list(s.form_violations.keys()) if s.form_violations else [],
         "sleep_hours": s.sleep_hours}
        for s in sessions
    ]
    risks = risk_analyzer.analyze(history)
    return {"risks": [{"name": r.name, "message": r.message,
                       "severity": r.severity, "recommendation": r.recommendation} for r in risks]}
