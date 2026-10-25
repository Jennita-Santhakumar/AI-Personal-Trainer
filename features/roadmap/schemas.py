"""
features/roadmap/schemas.py — Pydantic models & JSON schemas for roadmap generation.
"""
from __future__ import annotations
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


# ── Incoming User Request ───────────────────────────────────────────────────

class RoadmapRequest(BaseModel):
    goal: str = Field(
        ...,
        description="Primary fitness goal",
        pattern="^(strength|fat_loss|hypertrophy|endurance|athletic_performance|flexibility_mobility|body_recomposition)$"
    )
    level: str = Field(
        default="intermediate",
        description="Experience level",
        pattern="^(beginner|intermediate|advanced)$"
    )
    weeks: int = Field(default=4, ge=2, le=12, description="Roadmap duration in weeks")
    days_per_week: int = Field(default=4, ge=2, le=6, description="Training sessions per week")
    equipment: str = Field(
        default="full_gym",
        description="Available training equipment",
        pattern="^(full_gym|dumbbells_only|barbell_only|bodyweight|home_gym|kettlebells)$"
    )
    dietary_preference: str = Field(
        default="high_protein",
        description="Dietary archetype or preference",
        pattern="^(omnivore|high_protein|vegetarian|vegan|keto|paleo|mediterranean|pescatarian|balanced)$"
    )
    calorie_preference: Optional[str] = Field(
        default="moderate_deficit",
        description="Caloric target strategy",
        pattern="^(aggressive_deficit|moderate_deficit|maintenance|lean_bulk|surplus)$"
    )
    target_calories: Optional[int] = Field(default=None, ge=1000, le=6000)
    injuries: List[str] = Field(default_factory=list, description="Injuries or physical limitations")
    sport_focus: Optional[str] = Field(default="general", description="Specific sport or athletic specialty")
    target_focus_areas: List[str] = Field(default_factory=list, description="Priority body parts or skills")
    preferred_provider: Optional[str] = Field(
        default="auto",
        pattern="^(auto|gemini|groq|ollama|engine)$",
        description="Preferred LLM provider"
    )


class RoadmapProgressUpdate(BaseModel):
    task_id: str = Field(..., description="Unique task identifier, e.g. w1_d1_ex0 or w1_m1")
    completed: bool = Field(..., description="Completion state")


# ── Machine-Readable JSON Schema Models for LLM Output ──────────────────────

class ExerciseItem(BaseModel):
    id: str = Field(..., description="Exercise ID e.g. ex_bench_press")
    name: str = Field(..., description="Exercise display name")
    sets: int = Field(..., ge=1, le=10)
    reps: str = Field(..., description="e.g. '8-10', '12', 'AMRAP', '45s'")
    intensity: str = Field(..., description="e.g. 'RPE 8', '75% 1RM', 'Moderate pace'")
    rest_seconds: int = Field(default=90, description="Rest period in seconds")
    target_muscles: List[str] = Field(default_factory=list, description="Primary & secondary muscles")
    form_cues: List[str] = Field(default_factory=list, description="Key biomechanical coaching cues")
    pose_slug: Optional[str] = Field(default=None, description="Slug for Form AI pose detection if applicable")


class WorkoutDay(BaseModel):
    day_number: int = Field(..., ge=1, le=7)
    day_name: str = Field(..., description="e.g. 'Day 1: Upper Power & Chest Focus'")
    focus_area: str = Field(..., description="e.g. 'Chest & Triceps', 'Lower Body', 'Conditioning'")
    duration_minutes: int = Field(default=60)
    is_rest_day: bool = Field(default=False)
    warmup: List[str] = Field(default_factory=list, description="Specific dynamic warm-up drills")
    exercises: List[ExerciseItem] = Field(default_factory=list)
    cooldown: List[str] = Field(default_factory=list, description="Cooldown stretches & breathing")


class MealOption(BaseModel):
    name: str = Field(..., description="Dish name")
    calories: int = Field(..., ge=50, le=2500)
    protein_g: int = Field(..., ge=0, le=200)
    carbs_g: int = Field(..., ge=0, le=300)
    fat_g: int = Field(..., ge=0, le=150)
    ingredients: List[str] = Field(default_factory=list)
    recipe_tips: Optional[str] = None


class MealSlot(BaseModel):
    slot_id: str = Field(..., description="e.g. 'breakfast', 'lunch', 'pre_workout', 'dinner'")
    slot_title: str = Field(..., description="e.g. 'Power Breakfast', 'Pre-Workout Fuel'")
    time_window: str = Field(..., description="e.g. '07:30 - 08:30 AM'")
    options: List[MealOption] = Field(default_factory=list)


class DailyNutritionPlan(BaseModel):
    daily_calories: int = Field(..., ge=1000, le=6000)
    protein_g: int = Field(..., ge=30, le=400)
    carbs_g: int = Field(..., ge=20, le=700)
    fat_g: int = Field(..., ge=15, le=300)
    hydration_liters: float = Field(default=3.0)
    dietary_notes: str = Field(default="")
    meal_slots: List[MealSlot] = Field(default_factory=list)
    supplement_protocol: List[str] = Field(default_factory=list)


class WeeklyMilestone(BaseModel):
    title: str = Field(..., description="Target milestone title")
    description: str = Field(..., description="Target benchmark or progression check")
    metric_goal: str = Field(..., description="e.g. '+2.5kg squat', 'Run 5km sub-25m', 'Strict caloric adherence'")


class WeeklyModule(BaseModel):
    week_number: int = Field(..., ge=1, le=12)
    phase_name: str = Field(..., description="e.g. 'Phase 1: Foundation & Hypertrophy'")
    phase_focus: str = Field(..., description="e.g. 'Neuromuscular adaptation and volume priming'")
    workout_days: List[WorkoutDay] = Field(default_factory=list)
    nutrition_plan: DailyNutritionPlan
    milestones: List[WeeklyMilestone] = Field(default_factory=list)
    recovery_protocol: List[str] = Field(default_factory=list)


class MacroTargets(BaseModel):
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    hydration_liters: float


class FitnessRoadmapData(BaseModel):
    title: str = Field(..., description="Punchy roadmap title")
    goal: str
    level: str
    duration_weeks: int
    days_per_week: int
    overview_summary: str = Field(..., description="Comprehensive roadmap strategy and physiological methodology")
    target_macros: MacroTargets
    nutrition_guidelines: List[str] = Field(default_factory=list)
    key_habits: List[str] = Field(default_factory=list)
    weeks: List[WeeklyModule] = Field(default_factory=list)
