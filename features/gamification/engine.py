"""
features/gamification/engine.py — badges, streaks, points, injury risk analysis.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import Counter
from enum import Enum


class BadgeType(str, Enum):
    FIRST_WORKOUT    = "first_workout"
    STREAK_7         = "streak_7_days"
    STREAK_30        = "streak_30_days"
    STREAK_100       = "streak_100_days"
    PR_SQUAT         = "pr_squat"
    PR_BENCH         = "pr_bench"
    PR_DEADLIFT      = "pr_deadlift"
    FIRST_5K         = "first_5k_run"
    SUB_25_5K        = "5k_sub_25min"
    PERFECT_FORM_10  = "10_consecutive_good_form"
    FORM_IMPROVED    = "form_improvement"
    SESSIONS_10      = "10_sessions"
    SESSIONS_50      = "50_sessions"
    SESSIONS_100     = "100_sessions"
    ALL_ROUNDER      = "tried_4_activities"
    SWIMMER          = "swim_10_sessions"
    YOGI             = "yoga_10_sessions"
    EARLY_BIRD       = "early_bird_5_workouts"
    IRON_MIND        = "iron_mind_deload_completed"


@dataclass
class Badge:
    badge_type: BadgeType
    name: str
    description: str
    icon: str
    points: int
    earned_at: Optional[str] = None

    @property
    def earned(self) -> bool:
        return self.earned_at is not None

    def to_dict(self) -> dict:
        return {
            "type": self.badge_type.value, "name": self.name,
            "description": self.description, "icon": self.icon,
            "points": self.points, "earned_at": self.earned_at,
        }


BADGE_DEFINITIONS: Dict[BadgeType, Badge] = {
    BadgeType.FIRST_WORKOUT:   Badge(BadgeType.FIRST_WORKOUT,   "First Step",     "Completed your first workout",        "🌱", 50),
    BadgeType.STREAK_7:        Badge(BadgeType.STREAK_7,         "Week Warrior",   "7-day training streak",               "🔥", 100),
    BadgeType.STREAK_30:       Badge(BadgeType.STREAK_30,        "Iron Will",      "30-day training streak",              "⚡", 500),
    BadgeType.STREAK_100:      Badge(BadgeType.STREAK_100,       "Centurion",      "100-day training streak",             "🏆", 2000),
    BadgeType.PR_SQUAT:        Badge(BadgeType.PR_SQUAT,         "Squat PR",       "New squat personal record",           "👑", 200),
    BadgeType.PR_BENCH:        Badge(BadgeType.PR_BENCH,         "Bench PR",       "New bench press personal record",     "💪", 200),
    BadgeType.PR_DEADLIFT:     Badge(BadgeType.PR_DEADLIFT,      "Deadlift PR",    "New deadlift personal record",        "⚡", 200),
    BadgeType.FIRST_5K:        Badge(BadgeType.FIRST_5K,         "First 5k",       "Completed your first 5k run",         "🏃", 150),
    BadgeType.SUB_25_5K:       Badge(BadgeType.SUB_25_5K,        "Speed Demon",    "5k in under 25 minutes",             "💨", 300),
    BadgeType.PERFECT_FORM_10: Badge(BadgeType.PERFECT_FORM_10,  "Technician",     "10 sessions with zero form issues",   "✨", 300),
    BadgeType.SESSIONS_10:     Badge(BadgeType.SESSIONS_10,      "Getting Started","10 sessions logged",                  "💪", 100),
    BadgeType.SESSIONS_50:     Badge(BadgeType.SESSIONS_50,      "Committed",      "50 sessions logged",                  "🎯", 300),
    BadgeType.SESSIONS_100:    Badge(BadgeType.SESSIONS_100,     "Dedicated",      "100 sessions logged",                 "🌟", 1000),
    BadgeType.ALL_ROUNDER:     Badge(BadgeType.ALL_ROUNDER,      "All-Rounder",    "Tried 4 different activities",        "🎨", 150),
    BadgeType.SWIMMER:         Badge(BadgeType.SWIMMER,           "Swimmer",        "10 swimming sessions logged",         "🏊", 200),
    BadgeType.YOGI:            Badge(BadgeType.YOGI,              "Yogi",           "10 yoga sessions logged",             "🧘", 200),
    BadgeType.IRON_MIND:       Badge(BadgeType.IRON_MIND,         "Iron Mind",      "Completed a scheduled deload week",   "🧠", 100),
}

LEVEL_THRESHOLDS = [(0, "Beginner"), (500, "Novice"), (1500, "Intermediate"), (4000, "Advanced"), (10000, "Elite")]


@dataclass
class GamificationStateData:
    user_id: str
    points: int = 0
    streak: int = 0
    longest_streak: int = 0
    session_count: int = 0
    consecutive_good_form: int = 0
    badges_earned: List[str] = field(default_factory=list)
    activities_tried: List[str] = field(default_factory=list)
    last_session_date: Optional[str] = None

    @property
    def level(self) -> str:
        for threshold, name in reversed(LEVEL_THRESHOLDS):
            if self.points >= threshold:
                return name
        return "Beginner"

    @property
    def points_to_next_level(self) -> int:
        for threshold, _ in LEVEL_THRESHOLDS:
            if self.points < threshold:
                return threshold - self.points
        return 0

    @property
    def level_progress_pct(self) -> float:
        prev_t = 0
        for threshold, _ in LEVEL_THRESHOLDS:
            if self.points < threshold:
                span = threshold - prev_t
                gained = self.points - prev_t
                return round(gained / span, 3)
            prev_t = threshold
        return 1.0


class GamificationEngine:

    def process_session(
        self,
        state: GamificationStateData,
        activity: str,
        quality_score: Optional[float] = None,
        new_prs: Optional[Dict[str, float]] = None,
        is_deload_week: bool = False,
        run_distance_km: Optional[float] = None,
        run_time_minutes: Optional[float] = None,
    ) -> Tuple[GamificationStateData, List[Badge]]:
        """Process a session, update state, return (updated_state, newly_earned_badges)."""
        newly_earned: List[Badge] = []
        today = datetime.utcnow().date().isoformat()

        # ── Streak ────────────────────────────────────────────────────────────
        if state.last_session_date:
            gap = (datetime.utcnow().date() - datetime.fromisoformat(state.last_session_date).date()).days
            if gap == 1:
                state.streak += 1
            elif gap > 1:
                state.streak = 1
        else:
            state.streak = 1
        state.longest_streak = max(state.streak, state.longest_streak)
        state.last_session_date = today
        state.session_count += 1

        if activity not in state.activities_tried:
            state.activities_tried.append(activity)

        # ── Form consistency ──────────────────────────────────────────────────
        if quality_score is not None:
            state.consecutive_good_form = state.consecutive_good_form + 1 if quality_score >= 0.85 else 0

        # ── Points ────────────────────────────────────────────────────────────
        base = 20
        quality_bonus = int((quality_score or 0.5) * 30)
        streak_bonus = min(state.streak * 2, 20)
        state.points += base + quality_bonus + streak_bonus

        # ── Badge checks ──────────────────────────────────────────────────────
        checks: Dict[BadgeType, bool] = {
            BadgeType.FIRST_WORKOUT:   state.session_count >= 1,
            BadgeType.STREAK_7:        state.streak >= 7,
            BadgeType.STREAK_30:       state.streak >= 30,
            BadgeType.STREAK_100:      state.streak >= 100,
            BadgeType.SESSIONS_10:     state.session_count >= 10,
            BadgeType.SESSIONS_50:     state.session_count >= 50,
            BadgeType.SESSIONS_100:    state.session_count >= 100,
            BadgeType.PERFECT_FORM_10: state.consecutive_good_form >= 10,
            BadgeType.ALL_ROUNDER:     len(state.activities_tried) >= 4,
            BadgeType.SWIMMER:         state.activities_tried.count("swimming") >= 10,
            BadgeType.YOGI:            state.activities_tried.count("yoga") >= 10 or
                                       state.activities_tried.count("warrior2") >= 10,
            BadgeType.IRON_MIND:       is_deload_week,
        }
        if new_prs:
            checks[BadgeType.PR_SQUAT]    = "squat" in new_prs
            checks[BadgeType.PR_BENCH]    = "bench" in new_prs
            checks[BadgeType.PR_DEADLIFT] = "deadlift" in new_prs
        if run_distance_km and run_distance_km >= 5.0:
            checks[BadgeType.FIRST_5K] = True
        if run_distance_km and run_distance_km >= 5.0 and run_time_minutes and run_time_minutes < 25:
            checks[BadgeType.SUB_25_5K] = True

        for badge_type, condition in checks.items():
            if condition and badge_type.value not in state.badges_earned:
                badge = BADGE_DEFINITIONS[badge_type]
                import copy
                b = copy.copy(badge)
                b.earned_at = today
                state.badges_earned.append(badge_type.value)
                state.points += badge.points
                newly_earned.append(b)

        return state, newly_earned


# ── Injury risk analyzer ──────────────────────────────────────────────────────

@dataclass
class RiskSignal:
    name: str
    message: str
    severity: str   # warning | danger
    recommendation: str


class InjuryRiskAnalyzer:

    def analyze(self, session_history: List[dict]) -> List[RiskSignal]:
        risks = []

        # Volume spike (>30% increase week-on-week)
        if len(session_history) >= 14:
            this_week = sum(s.get("sets_completed", 0) for s in session_history[-7:])
            last_week = sum(s.get("sets_completed", 0) for s in session_history[-14:-7])
            if last_week > 0 and (this_week - last_week) / last_week > 0.30:
                risks.append(RiskSignal(
                    "high_volume_spike",
                    "Training volume increased more than 30% this week",
                    "warning",
                    "Consider adding an extra rest day or reducing intensity by 15%",
                ))

        # Consecutive high-RPE sessions
        consecutive_hard = 0
        for s in reversed(session_history):
            if (s.get("perceived_effort") or 0) >= 8:
                consecutive_hard += 1
            else:
                break
        if consecutive_hard >= 4:
            risks.append(RiskSignal(
                "consecutive_hard_days",
                f"{consecutive_hard} consecutive high-intensity sessions",
                "warning",
                "Insert an active recovery session or rest day before the next hard session",
            ))

        # Recurring form error
        all_errors = []
        for s in session_history[-10:]:
            all_errors.extend(s.get("form_violations", []))
        if all_errors:
            most_common, count = Counter(all_errors).most_common(1)[0]
            if count >= 3:
                risks.append(RiskSignal(
                    "recurring_form_error",
                    f"'{most_common.replace('_', ' ')}' detected in {count} of last 10 sessions",
                    "danger",
                    "Do not add load until this is corrected — book a technique session",
                ))

        # Low sleep + high load
        recent_3 = session_history[-3:]
        low_sleep = any((s.get("sleep_hours") or 8) < 6 for s in recent_3)
        high_load = any((s.get("perceived_effort") or 0) >= 8 for s in recent_3)
        if low_sleep and high_load:
            risks.append(RiskSignal(
                "low_sleep_high_load",
                "High training load combined with reported low sleep",
                "danger",
                "Prioritise 7-9 hours sleep tonight and reduce session intensity by 20%",
            ))

        return risks
