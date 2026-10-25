"""
tests/unit/test_workout_split.py — unit tests for the workout split generator.
"""
import pytest
from features.workout_split.generator import (
    WorkoutSplitGenerator, UserProfile, Goal, Level,
    ProgressiveOverloadEngine
)


@pytest.fixture
def generator():
    return WorkoutSplitGenerator()


@pytest.fixture
def basic_profile():
    return UserProfile(goal=Goal.STRENGTH, level=Level.INTERMEDIATE, days_per_week=3)


class TestGenerateSplit:
    def test_generates_correct_week_count(self, generator, basic_profile):
        splits = generator.generate(basic_profile, weeks=4)
        assert len(splits) == 4

    def test_week_numbers_sequential(self, generator, basic_profile):
        splits = generator.generate(basic_profile, weeks=4)
        for i, s in enumerate(splits, 1):
            assert s.week_number == i

    def test_days_match_days_per_week(self, generator, basic_profile):
        splits = generator.generate(basic_profile, weeks=1)
        assert len(splits[0].days) == basic_profile.days_per_week

    def test_all_goals_generate(self, generator):
        for goal in Goal:
            for days in (3, 4):
                profile = UserProfile(goal=goal, level=Level.BEGINNER, days_per_week=days)
                splits = generator.generate(profile, weeks=1)
                assert len(splits) == 1

    def test_injury_removes_exercises(self, generator):
        profile = UserProfile(goal=Goal.STRENGTH, level=Level.INTERMEDIATE,
                              days_per_week=3, injuries=["lower_back"])
        splits = generator.generate(profile, weeks=1)
        for day in splits[0].days:
            names = [e.name.lower() for e in day.exercises]
            assert not any("conventional deadlift" in n for n in names), \
                "Deadlift should be removed for lower_back injury"

    def test_deload_week_reduces_sets(self, generator):
        profile = UserProfile(goal=Goal.STRENGTH, level=Level.INTERMEDIATE, days_per_week=4)
        # Week 4 is a deload for intermediate (every 4th week)
        splits = generator.generate(profile, weeks=4)
        deload = splits[3]
        assert deload.deload is True
        for day in deload.days:
            for ex in day.exercises:
                assert ex.sets <= 4, "Deload sets should be reduced"

    def test_progressive_overload_note_present(self, generator, basic_profile):
        splits = generator.generate(basic_profile, weeks=4)
        for split in splits:
            assert len(split.overload_note) > 0

    def test_to_json_serializable(self, generator, basic_profile):
        import json
        splits = generator.generate(basic_profile, weeks=2)
        json_str = generator.to_json(splits)
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)
        assert len(parsed) == 2


class TestProgressiveOverload:
    def test_beginner_gets_highest_increase(self):
        eng = ProgressiveOverloadEngine()
        maxes = {"squat": 100.0, "bench": 70.0}
        new_maxes = eng.next_maxes(Level.BEGINNER, maxes)
        assert new_maxes["squat"] == pytest.approx(105.0, rel=0.01)

    def test_advanced_gets_smallest_increase(self):
        eng = ProgressiveOverloadEngine()
        maxes = {"squat": 200.0}
        new_maxes = eng.next_maxes(Level.ADVANCED, maxes)
        assert new_maxes["squat"] == pytest.approx(202.5, rel=0.01)

    def test_deload_on_cycle(self):
        eng = ProgressiveOverloadEngine()
        assert eng.deload_needed(4, Level.INTERMEDIATE) is True
        assert eng.deload_needed(3, Level.INTERMEDIATE) is False
        assert eng.deload_needed(6, Level.BEGINNER) is True
        assert eng.deload_needed(5, Level.BEGINNER) is False
