try:
    import pytest
except ImportError:
    pytest = None

import asyncio
from features.roadmap.schemas import RoadmapRequest, FitnessRoadmapData
from features.roadmap.generator import FitnessRoadmapGenerator, _generate_deterministic_roadmap


def test_deterministic_roadmap_generation():
    req = RoadmapRequest(
        goal="hypertrophy",
        level="intermediate",
        weeks=4,
        days_per_week=4,
        equipment="full_gym",
        dietary_preference="high_protein",
        calorie_preference="moderate_deficit",
    )
    profile = {
        "weight_kg": 78.0,
        "height_cm": 180.0,
        "age": 28,
    }
    raw = _generate_deterministic_roadmap(req, profile)
    assert raw is not None
    assert "weeks" in raw
    assert len(raw["weeks"]) == 4
    assert raw["target_macros"]["protein_g"] > 100
    assert raw["target_macros"]["calories"] > 1200

    # Validate with Pydantic model
    validated = FitnessRoadmapData(**raw)
    assert validated.duration_weeks == 4
    assert len(validated.weeks[0].workout_days) == 7


@pytest.mark.asyncio
async def test_roadmap_pipeline():
    generator = FitnessRoadmapGenerator()
    req = RoadmapRequest(
        goal="fat_loss",
        level="beginner",
        weeks=2,
        days_per_week=3,
        equipment="dumbbells_only",
        dietary_preference="vegetarian",
        preferred_provider="engine",
    )
    profile = {
        "weight_kg": 68.0,
        "height_cm": 165.0,
        "age": 24,
    }
    roadmap, provider = await generator.generate(req, profile)
    assert roadmap is not None
    assert roadmap.duration_weeks == 2
    assert len(roadmap.weeks) == 2
    assert roadmap.weeks[0].nutrition_plan.daily_calories > 1000
