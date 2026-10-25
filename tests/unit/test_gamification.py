"""
tests/unit/test_gamification.py — gamification engine tests.
"""
import pytest
from features.gamification.engine import (
    GamificationEngine, GamificationStateData, InjuryRiskAnalyzer, BadgeType
)


@pytest.fixture
def engine():
    return GamificationEngine()


@pytest.fixture
def fresh_state():
    return GamificationStateData(user_id="test-user-1")


class TestGamificationEngine:

    def test_first_session_earns_first_workout_badge(self, engine, fresh_state):
        updated, badges = engine.process_session(fresh_state, "squat", quality_score=0.8)
        badge_types = [b.badge_type for b in badges]
        assert BadgeType.FIRST_WORKOUT in badge_types

    def test_points_increase_after_session(self, engine, fresh_state):
        updated, _ = engine.process_session(fresh_state, "squat", quality_score=0.9)
        assert updated.points > 0

    def test_high_quality_gives_more_points(self, engine):
        s1 = GamificationStateData(user_id="u1")
        s2 = GamificationStateData(user_id="u2")
        high_q, _ = engine.process_session(s1, "squat", quality_score=1.0)
        low_q,  _ = engine.process_session(s2, "squat", quality_score=0.0)
        assert high_q.points > low_q.points

    def test_streak_increments_on_consecutive_days(self, engine, fresh_state):
        from datetime import datetime, timedelta
        fresh_state.last_session_date = (datetime.utcnow().date() - timedelta(days=1)).isoformat()
        fresh_state.streak = 5
        updated, _ = engine.process_session(fresh_state, "squat")
        assert updated.streak == 6

    def test_streak_resets_after_gap(self, engine, fresh_state):
        fresh_state.last_session_date = "2020-01-01"
        fresh_state.streak = 10
        updated, _ = engine.process_session(fresh_state, "squat")
        assert updated.streak == 1

    def test_streak_7_badge_awarded(self, engine, fresh_state):
        from datetime import datetime, timedelta
        fresh_state.last_session_date = (datetime.utcnow().date() - timedelta(days=1)).isoformat()
        fresh_state.streak = 6
        updated, badges = engine.process_session(fresh_state, "squat")
        assert BadgeType.STREAK_7 in [b.badge_type for b in badges]

    def test_badge_not_awarded_twice(self, engine, fresh_state):
        from datetime import datetime, timedelta
        fresh_state.last_session_date = (datetime.utcnow().date() - timedelta(days=1)).isoformat()
        fresh_state.streak = 6
        fresh_state.badges_earned = [BadgeType.STREAK_7.value]
        _, badges = engine.process_session(fresh_state, "squat")
        assert BadgeType.STREAK_7 not in [b.badge_type for b in badges]

    def test_pr_badge_awarded(self, engine, fresh_state):
        _, badges = engine.process_session(fresh_state, "squat", new_prs={"squat": 120.0})
        assert BadgeType.PR_SQUAT in [b.badge_type for b in badges]

    def test_level_is_beginner_at_zero(self, fresh_state):
        assert fresh_state.level == "Beginner"

    def test_level_advances_with_points(self, fresh_state):
        fresh_state.points = 600
        assert fresh_state.level == "Novice"
        fresh_state.points = 2000
        assert fresh_state.level == "Intermediate"

    def test_all_rounder_badge(self, engine, fresh_state):
        fresh_state.activities_tried = ["squat", "pushup", "yoga"]
        _, badges = engine.process_session(fresh_state, "swimming")
        assert BadgeType.ALL_ROUNDER in [b.badge_type for b in badges]

    def test_5k_badge_from_run_distance(self, engine, fresh_state):
        _, badges = engine.process_session(fresh_state, "running",
                                           run_distance_km=6.0, run_time_minutes=35)
        assert BadgeType.FIRST_5K in [b.badge_type for b in badges]

    def test_sub25_5k_badge(self, engine, fresh_state):
        _, badges = engine.process_session(fresh_state, "running",
                                           run_distance_km=5.1, run_time_minutes=24)
        badge_types = [b.badge_type for b in badges]
        assert BadgeType.SUB_25_5K in badge_types


class TestInjuryRiskAnalyzer:

    @pytest.fixture
    def analyzer(self):
        return InjuryRiskAnalyzer()

    def test_volume_spike_detected(self, analyzer):
        history = [{"sets_completed": 10, "perceived_effort": 6}] * 7 + \
                  [{"sets_completed": 20, "perceived_effort": 7}] * 7
        risks = analyzer.analyze(history)
        names = [r.name for r in risks]
        assert "high_volume_spike" in names

    def test_consecutive_hard_sessions_detected(self, analyzer):
        history = [{"sets_completed": 15, "perceived_effort": 9}] * 5
        risks = analyzer.analyze(history)
        names = [r.name for r in risks]
        assert "consecutive_hard_days" in names

    def test_recurring_form_error_detected(self, analyzer):
        history = [{"sets_completed": 10, "perceived_effort": 7,
                    "form_violations": ["knee_cave"]}] * 3
        risks = analyzer.analyze(history)
        names = [r.name for r in risks]
        assert "recurring_form_error" in names

    def test_no_risks_for_clean_history(self, analyzer):
        history = [{"sets_completed": 12, "perceived_effort": 6,
                    "form_violations": [], "sleep_hours": 8}] * 5
        risks = analyzer.analyze(history)
        assert len(risks) == 0
