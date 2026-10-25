"""
tasks.py — Celery background task definitions.
Start worker: celery -A tasks worker --loglevel=info
"""
from __future__ import annotations
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
import asyncio


# ── Lazy settings load — avoids import-time DB connection attempts ────────────

def _get_redis_url() -> str:
    from config import get_settings
    return get_settings().redis_url


celery_app = Celery(
    "fitness_platform",
    broker=_get_redis_url(),
    backend=_get_redis_url(),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,   # silence deprecation warning
    beat_schedule={
        "daily-briefings": {
            "task": "tasks.send_daily_briefings",
            "schedule": crontab(hour=7, minute=0),
        },
        "weekly-reviews": {
            "task": "tasks.send_weekly_reviews",
            "schedule": crontab(hour=21, minute=0, day_of_week=0),
        },
        "wearable-sync": {
            "task": "tasks.sync_all_wearables",
            "schedule": 7200,
        },
    },
)


def _run_async(coro):
    """Run an async coroutine from a Celery (sync) task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ── Tasks ─────────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_daily_briefing(self, user_id: str):
    async def _do():
        from database import AsyncSessionLocal
        from sqlalchemy import select
        from models import User, CoachConversation
        from features.coach.coach import AICoach
        from api.routers.coach import load_profile

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return
            profile = await load_profile(user, db)
            coach = AICoach()
            briefing = coach.daily_briefing(profile)
            db.add(CoachConversation(user_id=user_id, role="assistant", content=briefing))
            await db.commit()

    try:
        _run_async(_do())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def send_daily_briefings():
    async def _get_users():
        from database import AsyncSessionLocal
        from sqlalchemy import select
        from models import User
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User.id).where(User.is_active == True))
            return [row[0] for row in result.fetchall()]

    user_ids = _run_async(_get_users())
    for uid in user_ids:
        generate_daily_briefing.delay(uid)
    return {"dispatched": len(user_ids)}


@celery_app.task(bind=True, max_retries=2)
def sync_fitbit_for_user(self, user_id: str, date: str = None):
    date = date or datetime.utcnow().date().isoformat()

    async def _do():
        from database import AsyncSessionLocal
        from sqlalchemy import select
        from models import OAuthToken
        from features.metrics.tracker import FitbitConnector
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OAuthToken).where(
                    OAuthToken.user_id == user_id, OAuthToken.provider == "fitbit"
                )
            )
            token = result.scalar_one_or_none()
            if not token:
                return None
            connector = FitbitConnector(token.access_token)
            return await connector.get_daily_summary(date)

    try:
        return _run_async(_do())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def sync_all_wearables():
    async def _get_connected():
        from database import AsyncSessionLocal
        from sqlalchemy import select
        from models import OAuthToken
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OAuthToken.user_id).where(OAuthToken.provider == "fitbit")
            )
            return [row[0] for row in result.fetchall()]

    user_ids = _run_async(_get_connected())
    today = datetime.utcnow().date().isoformat()
    for uid in user_ids:
        sync_fitbit_for_user.delay(uid, today)
    return {"synced_users": len(user_ids)}


@celery_app.task(bind=True, max_retries=2)
def generate_weekly_review(self, user_id: str):
    async def _do():
        from database import AsyncSessionLocal
        from sqlalchemy import select
        from models import User, CoachConversation, WorkoutSession
        from features.coach.coach import AICoach
        from api.routers.coach import load_profile

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return
            cutoff = datetime.utcnow() - timedelta(days=7)
            sessions_r = await db.execute(
                select(WorkoutSession).where(
                    WorkoutSession.user_id == user_id,
                    WorkoutSession.created_at >= cutoff,
                )
            )
            week_sessions = sessions_r.scalars().all()
            total_cals = sum((s.metrics or {}).get("calories", 0) for s in week_sessions)
            profile = await load_profile(user, db)
            coach = AICoach()
            review = coach.weekly_review(
                profile, completed=len(week_sessions), planned=4,
                calories=total_cals, prs=[]
            )
            db.add(CoachConversation(
                user_id=user_id, role="assistant",
                content=f"[Weekly review]\n{review}",
            ))
            await db.commit()

    try:
        _run_async(_do())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def send_weekly_reviews():
    async def _get_users():
        from database import AsyncSessionLocal
        from sqlalchemy import select
        from models import User
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User.id).where(User.is_active == True))
            return [row[0] for row in result.fetchall()]

    user_ids = _run_async(_get_users())
    for uid in user_ids:
        generate_weekly_review.delay(uid)
    return {"dispatched": len(user_ids)}
