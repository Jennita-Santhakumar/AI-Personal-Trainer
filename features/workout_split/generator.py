"""
features/workout_split/generator.py
Full workout split generation engine with progressive overload.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum
import json


class Goal(str, Enum):
    STRENGTH    = "strength"
    FAT_LOSS    = "fat_loss"
    ENDURANCE   = "endurance"
    FLEXIBILITY = "flexibility"
    HYBRID      = "hybrid"


class Level(str, Enum):
    BEGINNER     = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED     = "advanced"


@dataclass
class UserProfile:
    goal: Goal
    level: Level
    days_per_week: int
    injuries: List[str] = field(default_factory=list)
    sport_focus: str = "general"
    age: int = 25
    weight_kg: float = 70.0
    current_maxes: Dict[str, float] = field(default_factory=dict)


@dataclass
class Exercise:
    name: str
    sets: int
    reps: str
    intensity: str
    rest_seconds: int
    notes: str = ""
    alternatives: List[str] = field(default_factory=list)
    muscle_groups: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class WorkoutDay:
    day_name: str
    session_name: str
    focus: str
    duration_minutes: int
    exercises: List[Exercise]
    warmup: List[str] = field(default_factory=list)
    cooldown: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "day_name": self.day_name,
            "session_name": self.session_name,
            "focus": self.focus,
            "duration_minutes": self.duration_minutes,
            "exercises": [e.to_dict() for e in self.exercises],
            "warmup": self.warmup,
            "cooldown": self.cooldown,
        }


@dataclass
class WeeklySplit:
    week_number: int
    days: List[WorkoutDay]
    overload_note: str
    deload: bool = False

    def to_dict(self) -> dict:
        return {
            "week_number": self.week_number,
            "days": [d.to_dict() for d in self.days],
            "overload_note": self.overload_note,
            "deload": self.deload,
        }


# ── Exercise database ─────────────────────────────────────────────────────────

EXERCISE_DB: Dict[str, Dict[str, Exercise]] = {
    "powerlifting": {
        "squat":      Exercise("Back squat", 5, "5", "RPE 8", 240, "Bar path over mid-foot", ["goblet squat", "front squat"], ["quads", "glutes", "core"]),
        "bench":      Exercise("Bench press", 5, "5", "RPE 8", 240, "Retract scapula, controlled descent", ["dumbbell press"], ["chest", "triceps", "shoulders"]),
        "deadlift":   Exercise("Conventional deadlift", 4, "3", "RPE 8", 300, "Push floor away, hinge at hip", ["trap bar DL"], ["hamstrings", "glutes", "back"]),
        "rdl":        Exercise("Romanian DL", 3, "8-10", "RPE 7", 180, "Feel hamstring stretch at bottom", [], ["hamstrings", "glutes"]),
        "paused_sq":  Exercise("Paused squat", 3, "3", "80% 1RM", 180, "2s pause at parallel", [], ["quads", "core"]),
        "ohp":        Exercise("Overhead press", 4, "6-8", "RPE 7", 180, "Squeeze glutes, neutral spine", [], ["shoulders", "triceps"]),
        "row":        Exercise("Barbell row", 4, "6-8", "RPE 7", 180, "Pull to lower chest, control eccentric", [], ["back", "biceps"]),
        "cgbp":       Exercise("Close-grip bench", 3, "8-10", "RPE 7", 150, "Elbows tucked, full lockout", [], ["triceps", "chest"]),
        "ghr":        Exercise("GHR / Nordic curl", 3, "6-8", "bodyweight", 120, "Slow eccentric", ["leg curl"], ["hamstrings"]),
        "hip_thrust": Exercise("Barbell hip thrust", 3, "10-12", "RPE 7", 120, "Full hip extension at top", [], ["glutes"]),
        "lat_pd":     Exercise("Lat pulldown", 3, "10-12", "moderate", 90, "Pull to upper chest", [], ["back", "biceps"]),
        "face_pull":  Exercise("Face pull", 3, "15-20", "light", 60, "External rotation cue", [], ["shoulders", "rotator cuff"]),
    },
    "running": {
        "easy_run":    Exercise("Easy run", 1, "30-45 min", "HR zone 2 (60-70% HRmax)", 0, "Conversational pace", [], ["cardiovascular"]),
        "tempo":       Exercise("Tempo run", 3, "8 min blocks", "HR zone 4 (80-87% HRmax)", 180, "Comfortably hard", [], ["cardiovascular"]),
        "intervals":   Exercise("400m repeats", 6, "400m", "5k pace", 90, "Consistent splits each rep", [], ["cardiovascular", "speed"]),
        "long_run":    Exercise("Long run", 1, "60-90 min", "HR zone 2", 0, "Fuel every 45 min if over 75 min", [], ["cardiovascular", "endurance"]),
        "strides":     Exercise("Strides", 4, "100m", "mile pace", 60, "Relaxed, smooth acceleration", [], ["speed", "neuromuscular"]),
        "hill_repeat": Exercise("Hill repeats", 6, "60s uphill", "hard effort", 120, "Drive knees, pump arms", [], ["strength", "cardiovascular"]),
        "recovery_run":Exercise("Recovery jog", 1, "20 min", "HR zone 1", 0, "Very easy — slower than you think", [], ["recovery"]),
    },
    "swimming": {
        "drills":    Exercise("Technique drills", 4, "50m", "easy", 30, "Catch-up, fingertip drag, side kick", [], ["technique"]),
        "main_set":  Exercise("Main aerobic set", 6, "100m", "moderate", 20, "Focus on stroke count per length", [], ["endurance"]),
        "kick_set":  Exercise("Kick set", 4, "50m", "easy-moderate", 20, "Kickboard, point toes", [], ["legs"]),
        "pull_set":  Exercise("Pull set", 4, "100m", "moderate", 20, "Pull buoy, focus on high elbow catch", [], ["arms", "technique"]),
        "sprint":    Exercise("Sprint set", 6, "25m", "maximal", 60, "Explosive push-off, maintain technique", [], ["speed"]),
        "endurance": Exercise("Endurance swim", 1, "800m", "steady", 60, "Even splits throughout", [], ["endurance"]),
        "IM_set":    Exercise("IM set", 4, "100m IM", "moderate", 30, "All 4 strokes: fly, back, breast, free", [], ["full body"]),
    },
    "yoga": {
        "sun_sal":    Exercise("Sun salutation A", 5, "rounds", "flow", 30, "Link breath to every movement", [], ["full body", "breath"]),
        "warriors":   Exercise("Warrior sequence", 1, "5 min", "hold 5 breaths", 10, "Warrior I, II, III", [], ["legs", "balance"]),
        "hip_open":   Exercise("Hip openers", 1, "10 min", "passive hold", 10, "Pigeon, lizard, frog pose", [], ["hips", "flexibility"]),
        "backbend":   Exercise("Backbend sequence", 1, "8 min", "active", 10, "Cobra, updog, bridge, wheel", [], ["spine", "chest"]),
        "balance":    Exercise("Balance sequence", 1, "5 min", "focused", 10, "Tree, eagle, standing split", [], ["balance", "core"]),
        "yin":        Exercise("Yin holds", 5, "3-5 min each", "passive", 0, "Full surrender in each pose", [], ["connective tissue", "flexibility"]),
        "breathwork": Exercise("Pranayama", 1, "10 min", "calm", 0, "Box breath or ujjayi breathing", [], ["nervous system"]),
        "core":       Exercise("Yoga core", 1, "8 min", "moderate", 30, "Plank, boat, side plank series", [], ["core"]),
    },
    "cardio": {
        "hiit":       Exercise("HIIT circuit", 4, "4 min on / 1 min off", "maximal effort", 60, "20s on 10s off tabata style", [], ["cardiovascular", "full body"]),
        "bike":       Exercise("Stationary bike", 1, "30 min", "moderate", 0, "Cadence 80-90 RPM", [], ["cardiovascular", "legs"]),
        "rowing":     Exercise("Rowing machine", 1, "20 min", "moderate", 0, "Drive with legs first, then back, then arms", [], ["full body", "cardiovascular"]),
        "jump_rope":  Exercise("Jump rope", 3, "5 min", "moderate-hard", 90, "Double unders if possible", [], ["cardiovascular", "coordination"]),
    },
}

INJURY_MODIFICATIONS = {
    "lower_back": {
        "remove":   ["conventional deadlift", "good morning", "squat"],
        "replace":  {"conventional deadlift": "trap bar deadlift", "squat": "goblet squat"},
        "add_note": "Avoid lumbar flexion under load. Brace core throughout. Hip hinge drill in warmup.",
    },
    "knee": {
        "remove":   ["squat", "lunge", "leg press", "step-up"],
        "replace":  {"squat": "box squat", "lunge": "hip thrust"},
        "add_note": "Knee tracks over toes. Avoid full flexion. Add terminal knee extension in warmup.",
    },
    "shoulder": {
        "remove":   ["bench press", "overhead press", "pull-up"],
        "replace":  {"bench press": "floor press", "overhead press": "landmine press"},
        "add_note": "Avoid overhead load. Add face pulls + band pull-aparts every session.",
    },
    "ankle": {
        "remove":   ["running", "jump rope", "hiit"],
        "replace":  {"running": "stationary bike", "hiit": "seated circuit"},
        "add_note": "Low-impact cardio only. Calf stretch and ankle mobility daily.",
    },
    "wrist": {
        "remove":   ["barbell row", "bench press"],
        "replace":  {"bench press": "dumbbell press (neutral grip)"},
        "add_note": "Neutral grip where possible. Wrist wraps for heavy pressing.",
    },
}


class ProgressiveOverloadEngine:
    WEEKLY_INCREASE = {Level.BEGINNER: 0.05, Level.INTERMEDIATE: 0.025, Level.ADVANCED: 0.0125}

    def next_maxes(self, level: Level, current: Dict[str, float]) -> Dict[str, float]:
        rate = self.WEEKLY_INCREASE[level]
        return {k: round(v * (1 + rate), 1) for k, v in current.items()}

    def deload_needed(self, week: int, level: Level) -> bool:
        cycle = 6 if level == Level.BEGINNER else 4
        return week % cycle == 0

    def overload_note(self, week: int, level: Level) -> str:
        if self.deload_needed(week, level):
            return "Deload week — reduce all loads to 50-60%, prioritise technique and recovery"
        rate = int(self.WEEKLY_INCREASE[level] * 100)
        return f"Add ~{rate}% to main lifts if all reps completed with good form (RPE ≤ 8)"


class WorkoutSplitGenerator:

    WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    TEMPLATES: Dict[Tuple, List[str]] = {
        (Goal.STRENGTH, 2):     ["lower_sq", "upper_bench"],
        (Goal.STRENGTH, 3):     ["lower_sq", "upper_bench", "lower_dl"],
        (Goal.STRENGTH, 4):     ["lower_sq", "upper_bench", "lower_dl", "upper_ohp"],
        (Goal.STRENGTH, 5):     ["lower_sq", "upper_bench", "lower_dl", "upper_ohp", "full_accessory"],
        (Goal.FAT_LOSS, 3):     ["full_strength", "cardio_hiit", "full_circuit"],
        (Goal.FAT_LOSS, 4):     ["upper", "lower", "cardio_hiit", "full_circuit"],
        (Goal.FAT_LOSS, 5):     ["upper", "lower", "cardio_hiit", "full_circuit", "yoga_flow"],
        (Goal.ENDURANCE, 3):    ["easy_run", "tempo", "long_run"],
        (Goal.ENDURANCE, 4):    ["easy_run", "intervals", "easy_run", "long_run"],
        (Goal.ENDURANCE, 5):    ["easy_run", "tempo", "easy_run", "intervals", "long_run"],
        (Goal.ENDURANCE, 6):    ["easy_run", "tempo", "easy_run", "intervals", "easy_run", "long_run"],
        (Goal.FLEXIBILITY, 3):  ["yoga_strength", "yoga_flow", "yoga_yin"],
        (Goal.FLEXIBILITY, 4):  ["yoga_flow", "yoga_strength", "yoga_yin", "yoga_flow"],
        (Goal.FLEXIBILITY, 5):  ["yoga_flow", "yoga_strength", "yoga_yin", "yoga_flow", "yoga_restore"],
        (Goal.HYBRID, 3):       ["lower_sq", "easy_run", "upper_bench"],
        (Goal.HYBRID, 4):       ["lower_sq", "easy_run", "upper_bench", "yoga_flow"],
        (Goal.HYBRID, 5):       ["lower_sq", "tempo", "upper_bench", "lower_dl", "yoga_yin"],
    }

    def generate(self, profile: UserProfile, weeks: int = 4) -> List[WeeklySplit]:
        overload = ProgressiveOverloadEngine()
        splits, current_maxes = [], dict(profile.current_maxes)
        for week in range(1, weeks + 1):
            is_deload = overload.deload_needed(week, profile.level)
            days = self._build_week(profile, is_deload)
            splits.append(WeeklySplit(week, days, overload.overload_note(week, profile.level), is_deload))
            if current_maxes and not is_deload:
                current_maxes = overload.next_maxes(profile.level, current_maxes)
        return splits

    def _build_week(self, p: UserProfile, deload: bool) -> List[WorkoutDay]:
        key = (p.goal, p.days_per_week)
        template = self.TEMPLATES.get(key) or self._closest_template(p.goal, p.days_per_week)
        days, workout_idx = [], 0
        for i, weekday in enumerate(self.WEEKDAYS):
            if workout_idx < len(template):
                day = self._build_day(weekday, template[workout_idx], p, deload)
                days.append(day)
                workout_idx += 1
                # Insert rest day spacing where appropriate
                if len(template) <= 4 and workout_idx in (2, 4):
                    pass  # handled by skipping some weekdays
        return days

    def _build_day(self, weekday: str, session_type: str, p: UserProfile, deload: bool) -> WorkoutDay:
        builders = {
            "lower_sq":      self._lower_squat,
            "lower_dl":      self._lower_deadlift,
            "upper_bench":   self._upper_bench,
            "upper_ohp":     self._upper_ohp,
            "full_accessory":self._accessory,
            "full_strength": self._full_body_strength,
            "upper":         self._upper_hypertrophy,
            "lower":         self._lower_hypertrophy,
            "cardio_hiit":   self._hiit,
            "full_circuit":  self._circuit,
            "easy_run":      self._easy_run,
            "tempo":         self._tempo_run,
            "long_run":      self._long_run,
            "intervals":     self._intervals,
            "yoga_flow":     self._yoga_flow,
            "yoga_strength": self._yoga_strength,
            "yoga_yin":      self._yoga_yin,
            "yoga_restore":  self._yoga_yin,
        }
        builder = builders.get(session_type, self._full_body_strength)
        day = builder(weekday, p)
        day = self._apply_injuries(day, p.injuries)
        if deload:
            for ex in day.exercises:
                ex.sets = max(2, int(ex.sets * 0.6))
                ex.intensity = ex.intensity.replace("RPE 8", "RPE 6").replace("RPE 7", "RPE 5").replace("80%", "60%").replace("75%", "55%")
        return day

    # ── Session builders ──────────────────────────────────────────────────────

    def _lower_squat(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["powerlifting"]
        intensity = {"beginner": "70% 1RM", "intermediate": "78% 1RM", "advanced": "RPE 8"}[p.level.value]
        sq = Exercise("Back squat", 5, "5", intensity, 240, "Bar path over mid-foot — record from side", ["goblet squat"], ["quads", "glutes"])
        return WorkoutDay(weekday, "Lower — Squat focus", "strength", 75,
            [sq, db["paused_sq"], db["rdl"], db["ghr"], db["hip_thrust"]],
            ["5 min bike", "Hip circle 2×10", "Goblet squat 2×5", "Box squat warmup"],
            ["Hip flexor 2 min/side", "Pigeon 90s/side", "Foam roll quads"])

    def _lower_deadlift(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["powerlifting"]
        intensity = {"beginner": "70% 1RM", "intermediate": "78% 1RM", "advanced": "RPE 8"}[p.level.value]
        dl = Exercise("Conventional deadlift", 4, "3", intensity, 300, "Push floor away — don't pull bar", ["trap bar DL"], ["hamstrings", "glutes", "back"])
        return WorkoutDay(weekday, "Lower — Deadlift focus", "strength", 75,
            [dl, db["rdl"], db["ghr"], Exercise("Leg press", 3, "10-12", "moderate", 120)],
            ["Hip hinge drill 2×10", "Cat-cow 10 reps", "Romanian DL empty bar 2×5"],
            ["Hamstring stretch 2 min/side", "Pigeon 90s/side", "Lower back child's pose"])

    def _upper_bench(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["powerlifting"]
        intensity = {"beginner": "70% 1RM", "intermediate": "78% 1RM", "advanced": "RPE 8"}[p.level.value]
        bp = Exercise("Bench press", 5, "5", intensity, 240, "Retract scapula — controlled 2s descent", ["dumbbell press"], ["chest", "triceps"])
        return WorkoutDay(weekday, "Upper — Bench focus", "strength", 70,
            [bp, db["row"], db["ohp"], db["cgbp"], db["face_pull"]],
            ["Band pull-apart 3×15", "Face pull 3×15", "Empty bar warmup sets"],
            ["Doorway chest stretch 90s", "Lat stretch 60s/side"])

    def _upper_ohp(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["powerlifting"]
        return WorkoutDay(weekday, "Upper — Press variety", "hypertrophy", 65,
            [db["ohp"], db["lat_pd"], db["cgbp"], db["row"],
             Exercise("Dumbbell curl", 3, "12-15", "RPE 7", 60, "", [], ["biceps"]),
             Exercise("Tricep pushdown", 3, "12-15", "RPE 7", 60, "", [], ["triceps"])],
            ["Shoulder circles 2×10", "Band pull-apart 2×20"],
            ["Overhead tricep stretch", "Cross-body shoulder stretch"])

    def _accessory(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["powerlifting"]
        return WorkoutDay(weekday, "Full body — Accessory", "hypertrophy", 60,
            [db["rdl"], db["row"], db["face_pull"],
             Exercise("Dumbbell lunges", 3, "10/leg", "RPE 7", 90),
             Exercise("Cable row", 3, "12-15", "RPE 7", 90),
             Exercise("Plank", 3, "60s", "bodyweight", 60)],
            ["5 min light cardio"],
            ["Full body stretch routine 10 min"])

    def _full_body_strength(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["powerlifting"]
        return WorkoutDay(weekday, "Full body strength", "strength", 60,
            [db["squat"], db["bench"], db["rdl"], db["row"]],
            ["5 min warmup cardio"],
            ["Stretch major muscle groups"])

    def _upper_hypertrophy(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["powerlifting"]
        return WorkoutDay(weekday, "Upper — Hypertrophy", "hypertrophy", 60,
            [db["bench"], db["row"], db["lat_pd"], db["ohp"],
             Exercise("Dumbbell fly", 3, "12-15", "RPE 7", 75),
             Exercise("Cable curl", 3, "12-15", "RPE 7", 60)],
            ["Shoulder warmup band work"],
            ["Upper body stretch"])

    def _lower_hypertrophy(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["powerlifting"]
        return WorkoutDay(weekday, "Lower — Hypertrophy", "hypertrophy", 60,
            [db["squat"], db["rdl"], db["hip_thrust"], db["ghr"],
             Exercise("Leg curl", 3, "12-15", "moderate", 75),
             Exercise("Calf raise", 4, "15-20", "moderate", 60)],
            ["5 min bike warmup", "Hip circles"],
            ["Quad and hamstring stretch"])

    def _hiit(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["cardio"]
        return WorkoutDay(weekday, "HIIT — Metabolic conditioning", "cardio", 40,
            [db["jump_rope"], db["hiit"],
             Exercise("Burpees", 4, "10 reps", "maximal", 60),
             Exercise("Mountain climbers", 3, "30s", "maximal", 45)],
            ["5 min easy jog", "Dynamic stretching"],
            ["5 min easy walk", "Static stretching"])

    def _circuit(self, weekday: str, p: UserProfile) -> WorkoutDay:
        return WorkoutDay(weekday, "Full body circuit", "cardio", 45,
            [Exercise("Squat to press", 3, "12 reps", "moderate", 30),
             Exercise("Push-up", 3, "12-15 reps", "bodyweight", 30),
             Exercise("Reverse lunge", 3, "10/leg", "moderate", 30),
             Exercise("Dumbbell row", 3, "12/arm", "moderate", 30),
             Exercise("Plank", 3, "45s", "bodyweight", 30)],
            ["5 min walk"], ["Full stretch"])

    def _easy_run(self, weekday: str, p: UserProfile) -> WorkoutDay:
        duration = {"beginner": "25 min", "intermediate": "40 min", "advanced": "55 min"}[p.level.value]
        return WorkoutDay(weekday, "Easy aerobic run", "endurance", 45,
            [EXERCISE_DB["running"]["easy_run"]],
            ["5 min walk", "Dynamic leg swings", "Ankle circles"],
            ["5 min walk", "Calf stretch 90s/side", "Hip flexor stretch"])

    def _tempo_run(self, weekday: str, p: UserProfile) -> WorkoutDay:
        reps = {"beginner": 2, "intermediate": 3, "advanced": 4}[p.level.value]
        return WorkoutDay(weekday, "Tempo run", "speed", 50,
            [Exercise("Warmup jog", 1, "10 min", "easy", 0),
             Exercise("Tempo blocks", reps, "8 min", "HR zone 4", 180, "Comfortably hard — not sprinting"),
             Exercise("Cooldown jog", 1, "8 min", "easy", 0)],
            ["Dynamic drills", "A-skips 2×20m", "High knees 2×20m"])

    def _long_run(self, weekday: str, p: UserProfile) -> WorkoutDay:
        dist = {"beginner": "5-7 km", "intermediate": "10-14 km", "advanced": "18-25 km"}[p.level.value]
        return WorkoutDay(weekday, "Long run", "endurance", 90,
            [Exercise("Long slow run", 1, dist, "HR zone 2 (conversational)", 0, "Gel/fuel every 45 min if over 75 min")],
            ["10 min easy warmup jog"],
            ["5 min walk", "Full leg stretch routine 10 min"])

    def _intervals(self, weekday: str, p: UserProfile) -> WorkoutDay:
        reps = {"beginner": 4, "intermediate": 6, "advanced": 8}[p.level.value]
        return WorkoutDay(weekday, "Speed — Intervals", "speed", 55,
            [Exercise("Warmup jog", 1, "12 min", "easy", 0),
             Exercise("400m repeats", reps, "400m", "5k pace (HR zone 5)", 90, "Consistent splits — don't go out too fast"),
             Exercise("Cooldown jog", 1, "10 min", "easy", 0)],
            ["Leg swings", "A-skips", "Build-up strides 3×80m"])

    def _yoga_flow(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["yoga"]
        return WorkoutDay(weekday, "Yoga — Vinyasa flow", "flexibility", 60,
            [db["sun_sal"], db["warriors"], db["balance"], db["core"], db["breathwork"]],
            ["Seated body scan 3 min"], ["Savasana 5 min"])

    def _yoga_strength(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["yoga"]
        return WorkoutDay(weekday, "Yoga — Strength & stability", "strength", 60,
            [db["sun_sal"], db["warriors"], db["backbend"], db["balance"], db["core"]],
            ["Child's pose 3 min"], ["Savasana 5 min"])

    def _yoga_yin(self, weekday: str, p: UserProfile) -> WorkoutDay:
        db = EXERCISE_DB["yoga"]
        return WorkoutDay(weekday, "Yoga — Yin / restore", "recovery", 60,
            [db["hip_open"], db["yin"], db["breathwork"]],
            ["Gentle cat-cow 5 min"], ["Savasana 8 min"])

    def _apply_injuries(self, day: WorkoutDay, injuries: List[str]) -> WorkoutDay:
        for injury in injuries:
            key = injury.lower().replace(" ", "_")
            mods = INJURY_MODIFICATIONS.get(key, {})
            if not mods:
                continue
            remove = [r.lower() for r in mods.get("remove", [])]
            replace = {k.lower(): v for k, v in mods.get("replace", {}).items()}
            note = mods.get("add_note", "")
            filtered = []
            for ex in day.exercises:
                ex_lower = ex.name.lower()
                if any(r in ex_lower for r in remove):
                    rep_key = next((k for k in replace if k in ex_lower), None)
                    if rep_key:
                        filtered.append(Exercise(replace[rep_key], ex.sets, ex.reps, ex.intensity, ex.rest_seconds, f"Modified for {injury}: {note}"))
                else:
                    filtered.append(ex)
            day.exercises = filtered
            if note and note not in day.warmup:
                day.warmup.append(f"Injury note: {note}")
        return day

    def _closest_template(self, goal: Goal, days: int) -> List[str]:
        candidates = [(g, d) for (g, d) in self.TEMPLATES if g == goal]
        if not candidates:
            return self.TEMPLATES[(Goal.STRENGTH, 3)]
        return self.TEMPLATES[min(candidates, key=lambda x: abs(x[1] - days))]

    def to_json(self, splits: List[WeeklySplit]) -> str:
        return json.dumps([s.to_dict() for s in splits], indent=2)
