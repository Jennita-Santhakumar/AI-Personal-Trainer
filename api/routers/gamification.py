"""
api/routers/gamification.py — badges, streaks, leaderboard, progress endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models import User, GamificationState, PersonalRecord
from api.middleware.auth import get_current_user
from features.gamification.engine import BADGE_DEFINITIONS, BadgeType, LEVEL_THRESHOLDS

router = APIRouter(prefix="/api/v1/gamification", tags=["gamification"])


@router.get("/status")
async def get_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(GamificationState).where(GamificationState.user_id == user.id))
    gam = result.scalar_one_or_none()
    if not gam:
        return {"points": 0, "streak": 0, "badges": [], "level": "Beginner"}

    # Determine current level and next threshold
    level = "Beginner"
    next_level_pts = 500
    for threshold, name in LEVEL_THRESHOLDS:
        if gam.points >= threshold:
            level = name
        else:
            next_level_pts = threshold
            break
    else:
        next_level_pts = LEVEL_THRESHOLDS[-1][0]  # already at max

    earned_badges = []
    for b_type_str in (gam.badges_earned or []):
        try:
            b_def = BADGE_DEFINITIONS[BadgeType(b_type_str)]
            earned_badges.append(b_def.to_dict())
        except (KeyError, ValueError):
            pass

    all_badges = []
    for badge_type, badge in BADGE_DEFINITIONS.items():
        b = badge.to_dict()
        b["earned"] = badge_type.value in (gam.badges_earned or [])
        all_badges.append(b)

    return {
        "points": gam.points,
        "streak": gam.streak,
        "longest_streak": gam.longest_streak,
        "session_count": gam.session_count,
        "level": level,
        "points_to_next_level": max(0, next_level_pts - gam.points),
        "level_threshold": next_level_pts,
        "badges_earned_count": len(gam.badges_earned or []),
        "badges": all_badges,
        "activities_tried": gam.activities_tried or [],
    }


@router.get("/personal-records")
async def personal_records(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PersonalRecord)
        .where(PersonalRecord.user_id == user.id)
        .order_by(PersonalRecord.achieved_at.desc())
    )
    prs = result.scalars().all()

    # Group by lift, return best per lift
    best: dict = {}
    for pr in prs:
        if pr.lift_name not in best or pr.value > best[pr.lift_name]["value"]:
            best[pr.lift_name] = {
                "lift": pr.lift_name,
                "value": pr.value,
                "achieved_at": pr.achieved_at.isoformat(),
                "session_id": pr.session_id,
            }
    return {"personal_records": list(best.values())}
