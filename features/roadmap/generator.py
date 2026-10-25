"""
features/roadmap/generator.py — LLM-driven fitness & nutrition roadmap generator.
Supports:
  1. Google Gemini API (gemini-1.5-flash / gemini-2.0-flash / gemini-1.5-pro)
  2. Groq API (llama-3.3-70b-versatile / llama-3.1-8b-instant)
  3. Ollama (local Docker or localhost endpoint)
  4. Algorithmic Science-Backed Engine (instant, deterministic fallback)
"""
from __future__ import annotations
import json
import re
import math
import uuid
import httpx
from typing import Dict, Any, Optional, Tuple, List

from config import get_settings
from features.roadmap.schemas import (
    RoadmapRequest,
    FitnessRoadmapData,
    WeeklyModule,
    WorkoutDay,
    ExerciseItem,
    DailyNutritionPlan,
    MealSlot,
    MealOption,
    WeeklyMilestone,
    MacroTargets,
)

settings = get_settings()


# ── Strict JSON Prompt Template ─────────────────────────────────────────────

ROADMAP_SYSTEM_PROMPT = """You are an elite exercise physiologist, strength & conditioning specialist, and registered sports dietitian.
Your task is to generate a comprehensive, personalized, multi-week Fitness and Nutrition Roadmap tailored specifically to the user's biometrics, goal, experience level, available equipment, schedule, and dietary restrictions.

IMPORTANT REQUIREMENTS:
1. You MUST respond ONLY with a single valid, well-formed JSON object conforming strictly to the requested JSON schema.
2. Do NOT output any introductory text, markdown commentary, explanations, or conclusions outside the JSON object.
3. Every exercise must include accurate set/rep ranges, intensities (RPE / %1RM), rest durations in seconds, target muscles, and concise biomechanical form cues.
4. If the user has injuries or joint restrictions, strictly replace contraindicated movements with safe, high-efficacy alternatives.
5. Every week must provide progressive overload (volume adjustments, intensity progression, or technical complexity).
6. Provide complete daily nutrition plans with specific caloric targets, macronutrient split (Protein, Carbs, Fat in grams), hydration goals in liters, and realistic meal slots with ingredient breakdowns and culinary preparation tips.
7. Include weekly milestones and recovery protocols for every week.

JSON SCHEMA STRUCTURE:
{
  "title": "string (e.g. 8-Week Hypertrophy & Recomposition Masterplan)",
  "goal": "string",
  "level": "string",
  "duration_weeks": int,
  "days_per_week": int,
  "overview_summary": "string (2-3 detailed paragraphs outlining the physiological phases, periodization method, and nutritional periodization)",
  "target_macros": {
    "calories": int,
    "protein_g": int,
    "carbs_g": int,
    "fat_g": int,
    "hydration_liters": float
  },
  "nutrition_guidelines": ["string", "string", ...],
  "key_habits": ["string", "string", ...],
  "weeks": [
    {
      "week_number": int,
      "phase_name": "string (e.g. Phase 1: Neuromuscular Priming)",
      "phase_focus": "string",
      "workout_days": [
        {
          "day_number": int,
          "day_name": "string (e.g. Day 1: Upper Body Power)",
          "focus_area": "string (e.g. Chest, Back & Delts)",
          "duration_minutes": int,
          "is_rest_day": bool,
          "warmup": ["string", "string", ...],
          "exercises": [
            {
              "id": "string",
              "name": "string",
              "sets": int,
              "reps": "string",
              "intensity": "string",
              "rest_seconds": int,
              "target_muscles": ["string", "string"],
              "form_cues": ["string", "string"],
              "pose_slug": "string or null (squat|bench|deadlift|overhead_press|pushup|pullup)"
            }
          ],
          "cooldown": ["string", "string", ...]
        }
      ],
      "nutrition_plan": {
        "daily_calories": int,
        "protein_g": int,
        "carbs_g": int,
        "fat_g": int,
        "hydration_liters": float,
        "dietary_notes": "string",
        "meal_slots": [
          {
            "slot_id": "string (breakfast|lunch|dinner|pre_workout|post_workout|snack)",
            "slot_title": "string",
            "time_window": "string",
            "options": [
              {
                "name": "string",
                "calories": int,
                "protein_g": int,
                "carbs_g": int,
                "fat_g": int,
                "ingredients": ["string", "string", ...],
                "recipe_tips": "string"
              }
            ]
          }
        ],
        "supplement_protocol": ["string", "string", ...]
      },
      "milestones": [
        {
          "title": "string",
          "description": "string",
          "metric_goal": "string"
        }
      ],
      "recovery_protocol": ["string", "string", ...]
    }
  ]
}
"""


def _build_user_prompt(req: RoadmapRequest, user_profile: Dict[str, Any]) -> str:
    injuries_str = ", ".join(req.injuries) if req.injuries else "None reported"
    focus_str = ", ".join(req.target_focus_areas) if req.target_focus_areas else "Overall balanced physique & performance"
    
    return f"""Generate a personalized {req.weeks}-week fitness and nutrition roadmap with the following specifications:

== ATHLETE BIOMETRIC PROFILE ==
- Goal: {req.goal}
- Experience Level: {req.level}
- Age: {user_profile.get('age', 26)} years
- Weight: {user_profile.get('weight_kg', 75.0)} kg
- Height: {user_profile.get('height_cm', 178.0)} cm
- Training Frequency: {req.days_per_week} days per week
- Available Equipment: {req.equipment}
- Program Duration: {req.weeks} weeks
- Dietary Archetype: {req.dietary_preference}
- Caloric Strategy: {req.calorie_preference or 'custom'} (Target Calories: {req.target_calories or 'calculate based on biometrics & goal'})
- Injuries / Joint Restrictions: {injuries_str}
- Sport / Athletic Specialty: {req.sport_focus or 'general fitness'}
- Priority Focus Areas: {focus_str}

== OUTPUT INSTRUCTIONS ==
Produce the complete JSON object for all {req.weeks} weeks. Ensure seamless progressive overload from Week 1 to Week {req.weeks}. Return strictly valid JSON.
"""


# ── JSON Sanitizer & Cleaner ────────────────────────────────────────────────

def _clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """Cleans markdown code fences, trailing comments, and repairs common LLM JSON defects."""
    cleaned = raw_text.strip()
    
    # Remove markdown ```json ... ``` wrapper if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    # Find matching JSON boundaries
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx : end_idx + 1]

    # Attempt standard parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Clean trailing commas before closing braces/brackets
        repaired = re.sub(r",\s*([}\]])", r"\1", cleaned)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM JSON response: {str(e)}")


def _enrich_task_ids(roadmap_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures each exercise, meal slot, and milestone has a deterministic unique ID for frontend tracking."""
    weeks = roadmap_dict.get("weeks", [])
    for w_idx, week in enumerate(weeks, 1):
        for d_idx, day in enumerate(week.get("workout_days", []), 1):
            for e_idx, ex in enumerate(day.get("exercises", [])):
                if not ex.get("id"):
                    ex["id"] = f"w{w_idx}_d{d_idx}_ex{e_idx}"
        
        nutrition = week.get("nutrition_plan", {})
        for m_idx, slot in enumerate(nutrition.get("meal_slots", []), 1):
            if not slot.get("slot_id"):
                slot["slot_id"] = f"w{w_idx}_meal_{m_idx}"
            for o_idx, opt in enumerate(slot.get("options", [])):
                opt["opt_id"] = f"w{w_idx}_m{m_idx}_opt{o_idx}"
        
        for ms_idx, ms in enumerate(week.get("milestones", []), 1):
            ms["id"] = f"w{w_idx}_ms_{ms_idx}"

    return roadmap_dict


# ── LLM Service Callers ──────────────────────────────────────────────────────

async def _call_gemini(system_prompt: str, user_prompt: str, settings_obj) -> Optional[Dict[str, Any]]:
    api_key = getattr(settings_obj, "gemini_api_key", "")
    if not api_key:
        return None
    
    model = getattr(settings_obj, "gemini_model", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.4,
            "maxOutputTokens": 8192
        }
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, json=payload)
        if r.status_code == 200:
            data = r.json()
            candidates = data.get("candidates", [])
            if candidates:
                content_parts = candidates[0].get("content", {}).get("parts", [])
                if content_parts:
                    text = content_parts[0].get("text", "")
                    return _clean_and_parse_json(text)
        else:
            print(f"[RoadmapGenerator] Gemini API error: {r.status_code} {r.text[:200]}")
    return None


async def _call_groq(system_prompt: str, user_prompt: str, settings_obj) -> Optional[Dict[str, Any]]:
    api_key = getattr(settings_obj, "groq_api_key", "")
    if not api_key:
        return None
    
    model = getattr(settings_obj, "groq_model", "llama-3.3-70b-versatile")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "max_tokens": 8000
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, json=payload, headers=headers)
        if r.status_code == 200:
            data = r.json()
            choices = data.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")
                return _clean_and_parse_json(text)
        else:
            print(f"[RoadmapGenerator] Groq API error: {r.status_code} {r.text[:200]}")
    return None


async def _call_ollama(system_prompt: str, user_prompt: str, settings_obj) -> Optional[Dict[str, Any]]:
    ollama_url = getattr(settings_obj, "ollama_url", "http://ollama:11434").rstrip("/")
    model = getattr(settings_obj, "coach_model", "llama3.1:8b")
    
    # Try chat endpoint
    url = f"{ollama_url}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 7000}
    }
    
    # Also support fallback to localhost if container host isn't resolved
    urls_to_try = [url, "http://localhost:11434/api/chat", "http://127.0.0.1:11434/api/chat"]
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        for target_url in urls_to_try:
            try:
                r = await client.post(target_url, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    text = data.get("message", {}).get("content", "")
                    if text:
                        return _clean_and_parse_json(text)
            except Exception:
                continue
    return None


# ── Science-Backed Algorithmic Roadmap Fallback Generator ───────────────────

def _generate_deterministic_roadmap(req: RoadmapRequest, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    State-of-the-art algorithmic generator that crafts a fully customized,
    evidence-based multi-week workout and nutrition roadmap when LLM APIs are offline.
    """
    weight_kg = user_profile.get("weight_kg") or 72.0
    height_cm = user_profile.get("height_cm") or 175.0
    age = user_profile.get("age") or 25
    goal = req.goal
    level = req.level
    weeks_count = req.weeks
    days_pw = req.days_per_week
    equipment = req.equipment
    diet_pref = req.dietary_preference

    # Calculate BMR (Mifflin-St Jeor) & TDEE
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    activity_multiplier = 1.35 + (days_pw * 0.05)
    tdee = int(bmr * activity_multiplier)

    # Caloric target & macro split
    if goal in ("fat_loss", "body_recomposition"):
        deficit = 400 if req.calorie_preference == "moderate_deficit" else 600
        target_calories = max(1400, tdee - deficit)
        protein_g = int(weight_kg * 2.2) # High protein for muscle retention
        fat_g = int((target_calories * 0.25) / 9)
        carbs_g = int((target_calories - (protein_g * 4 + fat_g * 9)) / 4)
    elif goal in ("hypertrophy", "strength"):
        surplus = 300 if req.calorie_preference in ("lean_bulk", "surplus") else 150
        target_calories = tdee + surplus
        protein_g = int(weight_kg * 2.0)
        fat_g = int((target_calories * 0.25) / 9)
        carbs_g = int((target_calories - (protein_g * 4 + fat_g * 9)) / 4)
    elif goal == "endurance":
        target_calories = tdee + 150
        protein_g = int(weight_kg * 1.6)
        fat_g = int((target_calories * 0.22) / 9)
        carbs_g = int((target_calories - (protein_g * 4 + fat_g * 9)) / 4)
    else: # flexibility, general
        target_calories = tdee
        protein_g = int(weight_kg * 1.7)
        fat_g = int((target_calories * 0.27) / 9)
        carbs_g = int((target_calories - (protein_g * 4 + fat_g * 9)) / 4)

    if req.target_calories:
        target_calories = req.target_calories
        protein_g = int(weight_kg * 2.0)
        fat_g = int((target_calories * 0.25) / 9)
        carbs_g = max(50, int((target_calories - (protein_g * 4 + fat_g * 9)) / 4))

    hydration = round(max(2.5, weight_kg * 0.04), 1)

    # Title & Strategy
    goal_titles = {
        "strength": "Maximal Strength & Powerlifting Periodization Roadmap",
        "fat_loss": "Metabolic Conditioning & Lean Definition Roadmap",
        "hypertrophy": "Hypertrophy Volume & Progressive Overload Roadmap",
        "endurance": "Aerobic Capacity & Speed Endurance Architecture",
        "athletic_performance": "High-Performance Athletic Conditioning Blueprint",
        "flexibility_mobility": "Functional Mobility, Joint Longevity & Core Protocol",
        "body_recomposition": "Precision Body Recomposition & Muscle Sculpting Roadmap",
    }
    title = f"{weeks_count}-Week {goal_titles.get(goal, 'Comprehensive Athletic Performance Roadmap')}"
    
    overview = (
        f"This tailored {weeks_count}-week periodized roadmap is scientifically optimized for {level.upper()} level "
        f"athletes targeting {goal.replace('_', ' ')}. Training is scheduled across {days_pw} sessions per week with "
        f"structured progressive overload across compound movement patterns. The nutritional strategy establishes an optimal "
        f"daily intake of {target_calories} kcal ({protein_g}g Protein, {carbs_g}g Carbs, {fat_g}g Fat) with {hydration}L "
        f"daily hydration to maximize muscle protein synthesis and accelerate systemic recovery."
    )

    # Exercise templates by equipment & focus
    exercise_pools = {
        "push": [
            {"name": "Barbell Bench Press", "slug": "bench", "muscles": ["Chest", "Front Delts", "Triceps"], "cues": ["Retract scapulae", "Leg drive through floor", "Controlled eccentric"]},
            {"name": "Incline Dumbbell Press", "slug": "bench", "muscles": ["Upper Chest", "Anterior Delts"], "cues": ["30-degree incline", "Elbows at 45 degrees", "Full stretch at bottom"]},
            {"name": "Overhead Barbell Press", "slug": "overhead_press", "muscles": ["Shoulders", "Upper Traps", "Core"], "cues": ["Brace glutes and abs", "Head through window at lockout", "No lumbar hyperextension"]},
            {"name": "Dips or Triceps Pressdowns", "slug": "pushup", "muscles": ["Triceps", "Lower Chest"], "cues": ["Lean slightly forward", "Lock out triceps cleanly", "Smooth cadence"]},
            {"name": "Lateral Dumbbell Raises", "slug": None, "muscles": ["Lateral Deltoid"], "cues": ["Lead with elbows", "Slight forward torso pitch", "Pause at apex"]},
        ],
        "pull": [
            {"name": "Conventional Deadlift", "slug": "deadlift", "muscles": ["Posterior Chain", "Hamstrings", "Lats", "Erectors"], "cues": ["Hips back, wedge into bar", "Push floor away", "Lockout with glutes"]},
            {"name": "Barbell Bent-Over Row", "slug": None, "muscles": ["Lats", "Rhomboids", "Biceps"], "cues": ["45-degree hip hinge", "Pull to lower sternum", "Do not jerk torso"]},
            {"name": "Weighted / Bodyweight Pull-Ups", "slug": "pullup", "muscles": ["Lats", "Biceps", "Brachialis"], "cues": ["Depress shoulder blades first", "Chest to bar", "Dead hang descent"]},
            {"name": "Chest-Supported Dumbbell Row", "slug": None, "muscles": ["Mid-Back", "Rear Delts"], "cues": ["Drive elbows behind torso", "Squeeze shoulder blades", "2s isometric hold"]},
            {"name": "Face Pulls with Rope", "slug": None, "muscles": ["Rear Delts", "Rotator Cuff"], "cues": ["Pull rope to eye level", "External rotation at apex", "High repetition focus"]},
        ],
        "legs": [
            {"name": "Barbell Back Squat", "slug": "squat", "muscles": ["Quadriceps", "Glutes", "Adductors", "Core"], "cues": ["Knees track over toes", "Break at hips and knees simultaneously", "Drive out of hole"]},
            {"name": "Romanian Deadlift (RDL)", "slug": "deadlift", "muscles": ["Hamstrings", "Glute Max"], "cues": ["Soft knees, push hips back", "Feel hamstring tension", "Maintain neutral spine"]},
            {"name": "Bulgarian Split Squats", "slug": "squat", "muscles": ["Quads", "Gluteus Medius"], "cues": ["Stay upright for quads / lean forward for glutes", "Deep knee flexion", "Control balance"]},
            {"name": "Leg Curl / Nordic Hamstring", "slug": None, "muscles": ["Hamstrings"], "cues": ["Full knee flexion", "3s eccentric lowering", "No lower back arch"]},
            {"name": "Standing Calf Raises", "slug": None, "muscles": ["Gastrocnemius", "Soleus"], "cues": ["Full stretch at bottom", "Elevate on big toes", "2s pause at peak"]},
        ],
        "full_body": [
            {"name": "Front Squat / Goblet Squat", "slug": "squat", "muscles": ["Quads", "Core"], "cues": ["Elbows high", "Torso vertical", "Hit parallel depth"]},
            {"name": "Dumbbell Incline Bench Press", "slug": "bench", "muscles": ["Upper Chest", "Triceps"], "cues": ["Control descent", "Drive through palms", "Neutral wrist"]},
            {"name": "Trap Bar / Dumbbell Deadlift", "slug": "deadlift", "muscles": ["Glutes", "Hamstrings", "Quads"], "cues": ["Chest tall", "Drive through midfoot", "Solid brace"]},
            {"name": "Neutral-Grip Lat Pulldown", "slug": "pullup", "muscles": ["Lats", "Biceps"], "cues": ["Pull elbows to pockets", "Controlled return", "Open ribcage"]},
            {"name": "Plank with Shoulder Taps", "slug": None, "muscles": ["Core", "Anti-Rotation"], "cues": ["Lock hips in place", "Squeeze glutes", "Slow tempo"]},
        ],
    }

    # Dietary recipes tailored to preference
    meal_archetypes = {
        "high_protein": [
            {"slot": "breakfast", "title": "High-Protein Power Breakfast", "time": "07:30 AM", "name": "Egg White & Turkey Scramble with Avocado Toast", "cals": 480, "p": 42, "c": 38, "f": 18, "ing": ["4 Egg whites + 2 whole eggs", "60g lean turkey breast", "1 slice sourdough toast", "1/4 avocado", "Spinach"], "tips": "Cook eggs on low heat for creaminess. Top with hot sauce or everything seasoning."},
            {"slot": "pre_workout", "title": "Pre-Workout Fuel", "time": "11:30 AM", "name": "Greek Yogurt Berry Parfait with Chia Seeds", "cals": 320, "p": 28, "c": 40, "f": 5, "ing": ["200g 0% Greek Yogurt", "80g blueberries", "15g chia seeds", "1 tsp honey"], "tips": "Consume 60-90 minutes prior to training session for sustained glycogen delivery."},
            {"slot": "lunch", "title": "Lean Muscle Lunch", "time": "01:30 PM", "name": "Flame-Grilled Chicken Breast with Quinoa & Roasted Veggies", "cals": 620, "p": 54, "c": 58, "f": 16, "ing": ["180g chicken breast", "120g cooked quinoa", "150g broccoli & bell peppers", "1 tbsp olive oil", "Lemon herb marinade"], "tips": "Batch grill chicken breasts for 3 days to maintain effortless meal consistency."},
            {"slot": "post_workout", "title": "Post-Workout Recovery", "time": "05:00 PM", "name": "Whey Isolate Shake with Banana & Rice Cakes", "cals": 290, "p": 32, "c": 36, "f": 2, "ing": ["1 scoop Whey Protein Isolate", "1 medium banana", "2 lightly salted rice cakes"], "tips": "Rapidly absorbed amino acids and fast-acting carbs optimize muscle glycogen replenishment."},
            {"slot": "dinner", "title": "Restorative Dinner", "time": "07:45 PM", "name": "Baked Atlantic Salmon with Sweet Potato & Asparagus", "cals": 650, "p": 48, "c": 46, "f": 24, "ing": ["170g wild salmon fillet", "200g roasted sweet potato cubes", "120g grilled asparagus", "Garlic & dill glaze"], "tips": "Rich in Omega-3 fatty acids to reduce systemic exercise-induced inflammation."},
        ],
        "vegetarian": [
            {"slot": "breakfast", "title": "Protein Oatmeal Bowl", "time": "08:00 AM", "name": "Peanut Butter & Plant Protein Super-Oats", "cals": 510, "p": 36, "c": 56, "f": 16, "ing": ["60g rolled oats", "1 scoop plant protein", "1 tbsp peanut butter", "1/2 banana", "Hemp hearts"], "tips": "Mix protein powder after oats are cooked with warm almond milk."},
            {"slot": "lunch", "title": "Mediterranean Grain Bowl", "time": "01:00 PM", "name": "Grilled Tofu & Chickpea Buddha Bowl with Tahini", "cals": 580, "p": 38, "c": 62, "f": 20, "ing": ["150g firm pressed tofu", "100g chickpeas", "100g brown rice", "Cucumbers, tomatoes, kale", "Lemon tahini dressing"], "tips": "Press tofu for 20 minutes and air-fry at 200°C for crispy texture."},
            {"slot": "dinner", "title": "High-Protein Lentil Stew", "time": "08:00 PM", "name": "Rich Red Lentil & Paneer/Tempeh Curry with Spinach", "cals": 640, "p": 44, "c": 60, "f": 22, "ing": ["120g red lentils", "100g light paneer or tempeh", "Coconut milk splash", "Spinach", "Turmeric & ginger"], "tips": "Turmeric provides potent anti-inflammatory curcumin for recovery."},
        ],
        "vegan": [
            {"slot": "breakfast", "title": "Vegan Power Tofu Scramble", "time": "07:30 AM", "name": "Turmeric Spiced Tofu Scramble with Sourdough & Greens", "cals": 460, "p": 32, "c": 42, "f": 16, "ing": ["200g firm tofu", "Nutritional yeast (2 tbsp)", "Black salt (kala namak)", "Spinach", "Whole grain toast"], "tips": "Kala namak gives authentic egg aroma. Nutritional yeast provides essential B12."},
            {"slot": "lunch", "title": "Seitan & Edamame Quinoa Bowl", "time": "01:00 PM", "name": "Teriyaki Seitan Strips with Edamame & Steamed Broccoli", "cals": 620, "p": 52, "c": 64, "f": 14, "ing": ["140g seitan strips", "100g shelled edamame", "120g cooked quinoa", "Broccoli florets", "Low-sodium teriyaki"], "tips": "Seitan provides exceptional protein density for plant-based strength athletes."},
            {"slot": "dinner", "title": "Tempeh & Black Bean Burrito Bowl", "time": "07:30 PM", "name": "Smoky Grilled Tempeh with Black Beans, Guacamole & Salsa", "cals": 590, "p": 40, "c": 62, "f": 20, "ing": ["130g marinated tempeh", "120g black beans", "Brown rice", "Fajita peppers", "Fresh guacamole"], "tips": "Fermented tempeh supports optimal gut microbiome and high bioavailability."},
        ],
    }

    selected_meals = meal_archetypes.get(diet_pref, meal_archetypes["high_protein"])

    # Generate multi-week progression
    weeks_data: List[Dict[str, Any]] = []
    
    phases = [
        {"name": "Phase 1: Foundation & Neuromuscular Priming", "focus": "Movement pattern mastery, base conditioning, and metabolic priming"},
        {"name": "Phase 2: Volume Accretion & Hypertrophic Drive", "focus": "Progressive load increase, set volume expansion, and metabolic density"},
        {"name": "Phase 3: High-Intensity Overload & Peaking", "focus": "Peak intensity, maximal motor unit recruitment, and threshold endurance"},
        {"name": "Phase 4: Deload & Supercompensation", "focus": "Systemic fatigue dissipation, connective tissue recovery, and adaptation realization"},
    ]

    for w in range(1, weeks_count + 1):
        phase_idx = min(len(phases) - 1, (w - 1) // 2 if weeks_count > 4 else (w - 1) % len(phases))
        phase_info = phases[phase_idx]

        # Overload parameters by week
        rep_scheme = "8-10 reps" if w == 1 else "6-8 reps" if w == 2 else "5-6 reps" if w == 3 else "10-12 reps (controlled)"
        intensity_val = f"RPE {min(9, 7 + (w % 3))}"
        
        # Build workout days
        workout_days = []
        if days_pw == 3:
            splits_map = [("Day 1: Full Body Power", "full_body"), ("Day 2: Full Body Hypertrophy", "full_body"), ("Day 3: Full Body Density", "full_body")]
        elif days_pw == 4:
            splits_map = [("Day 1: Upper Power Focus", "push"), ("Day 2: Lower Quad & Posterior", "legs"), ("Day 3: Upper Hypertrophy", "pull"), ("Day 4: Lower Strength & Core", "legs")]
        elif days_pw == 5:
            splits_map = [("Day 1: Push (Chest, Shoulders, Triceps)", "push"), ("Day 2: Pull (Back, Rear Delts, Biceps)", "pull"), ("Day 3: Legs & Core", "legs"), ("Day 4: Upper Power", "push"), ("Day 5: Lower Density & Arms", "legs")]
        else: # 6 days
            splits_map = [("Day 1: Push A", "push"), ("Day 2: Pull A", "pull"), ("Day 3: Legs A", "legs"), ("Day 4: Push B", "push"), ("Day 5: Pull B", "pull"), ("Day 6: Legs B", "legs")]

        for d_num, (d_name, split_type) in enumerate(splits_map, 1):
            ex_list = exercise_pools.get(split_type, exercise_pools["full_body"])
            day_exercises = []
            for e_idx, base_ex in enumerate(ex_list):
                sets_count = 3 if w < 3 else 4
                day_exercises.append({
                    "id": f"w{w}_d{d_num}_ex{e_idx}",
                    "name": base_ex["name"],
                    "sets": sets_count,
                    "reps": rep_scheme,
                    "intensity": intensity_val,
                    "rest_seconds": 90 if "Squat" in base_ex["name"] or "Deadlift" in base_ex["name"] else 60,
                    "target_muscles": base_ex["muscles"],
                    "form_cues": base_ex["cues"],
                    "pose_slug": base_ex.get("slug")
                })
            
            workout_days.append({
                "day_number": d_num,
                "day_name": d_name,
                "focus_area": d_name.split(":")[-1].strip(),
                "duration_minutes": 55 + (w * 2),
                "is_rest_day": False,
                "warmup": [
                    "5 min low-intensity bike or row",
                    "90s World's Greatest Stretch",
                    "10 Banded shoulder dislocates & face pulls",
                    "2 ramp-up warmup sets before compound movement"
                ],
                "exercises": day_exercises,
                "cooldown": [
                    "3 min nasal diaphragmatic box breathing (4s in, 4s hold, 4s out, 4s hold)",
                    "Hamstring & hip flexor static stretch (45s per side)",
                    "Child's pose & lat release (60s)"
                ]
            })

        # Add rest / active recovery days to complete 7 days
        for r_num in range(days_pw + 1, 8):
            workout_days.append({
                "day_number": r_num,
                "day_name": f"Day {r_num}: Active Recovery & Mobility",
                "focus_area": "Mobility, Walking & Parasympathetic Recovery",
                "duration_minutes": 30,
                "is_rest_day": True,
                "warmup": ["5 min dynamic joint circles"],
                "exercises": [
                    {
                        "id": f"w{w}_d{r_num}_ex0",
                        "name": "Zone 2 Outdoor Walk / Light Stationary Cycle",
                        "sets": 1,
                        "reps": "30-45 min",
                        "intensity": "Zone 2 (Heart Rate 110-130 BPM)",
                        "rest_seconds": 0,
                        "target_muscles": ["Cardiovascular System", "Legs"],
                        "form_cues": ["Maintain purely nasal breathing", "Keep conversation pace effortlessly"],
                        "pose_slug": None
                    },
                    {
                        "id": f"w{w}_d{r_num}_ex1",
                        "name": "Full-Body Mobility Flow & Foam Rolling",
                        "sets": 1,
                        "reps": "15 min",
                        "intensity": "Restorative",
                        "rest_seconds": 0,
                        "target_muscles": ["Hips", "Thoracic Spine", "Hamstrings"],
                        "form_cues": ["Deep diaphragmatic breaths", "Do not rush transitions"],
                        "pose_slug": None
                    }
                ],
                "cooldown": ["10 min contrast shower or sauna (optional)"]
            })

        # Weekly meal slots
        slots = []
        for s_idx, m in enumerate(selected_meals, 1):
            slots.append({
                "slot_id": f"w{w}_meal_{s_idx}",
                "slot_title": m["title"],
                "time_window": m["time"],
                "options": [
                    {
                        "name": m["name"],
                        "calories": m["cals"],
                        "protein_g": m["p"],
                        "carbs_g": m["c"],
                        "fat_g": m["f"],
                        "ingredients": m["ing"],
                        "recipe_tips": m["tips"]
                    }
                ]
            })

        # Weekly milestones
        milestones = [
            {
                "title": f"Week {w} Progressive Target",
                "description": f"Log all scheduled workouts and maintain strict form quality on compound lifts.",
                "metric_goal": f"Complete {days_pw}/{days_pw} sessions with zero missed sets."
            },
            {
                "title": f"Week {w} Nutritional Adherence",
                "description": f"Hit daily protein target within +/- 10g and reach {hydration}L hydration daily.",
                "metric_goal": f"7/7 days consistent macro logging."
            }
        ]

        weeks_data.append({
            "week_number": w,
            "phase_name": phase_info["name"],
            "phase_focus": phase_info["focus"],
            "workout_days": workout_days,
            "nutrition_plan": {
                "daily_calories": target_calories,
                "protein_g": protein_g,
                "carbs_g": carbs_g,
                "fat_g": fat_g,
                "hydration_liters": hydration,
                "dietary_notes": f"High bioavailability {diet_pref.replace('_', ' ')} protocol structured around training peri-workout nutrition.",
                "meal_slots": slots,
                "supplement_protocol": [
                    "Creatine Monohydrate: 5g daily (any time with water)",
                    "Vitamin D3 + K2: 2,000-5,000 IU with morning meal",
                    "Omega-3 Fish Oil or Algae Oil: 2g EPA/DHA daily",
                    "Magnesium Glycinate: 300mg 45 min before sleep"
                ]
            },
            "milestones": milestones,
            "recovery_protocol": [
                "Target 7.5 - 8.5 hours of uninterrupted sleep per night",
                "Keep sleep environment dark and below 19°C (66°F)",
                "Cease caffeine consumption 9 hours prior to bedtime",
                "Perform 10 min morning sunlight exposure upon waking"
            ]
        })

    roadmap_dict = {
        "title": title,
        "goal": goal,
        "level": level,
        "duration_weeks": weeks_count,
        "days_per_week": days_pw,
        "overview_summary": overview,
        "target_macros": {
            "calories": target_calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
            "hydration_liters": hydration
        },
        "nutrition_guidelines": [
            f"Prioritize lean protein sources at every meal (aim for ~35-50g protein per major feeding window).",
            f"Front-load 60% of daily carbohydrates into the 4-hour window surrounding your workout.",
            f"Drink a minimum of 500ml water immediately upon waking to rehydrate.",
            f"Limit ultra-processed sugars and industrial seed oils to optimize metabolic flexibility."
        ],
        "key_habits": [
            "Log every exercise set and rep in the roadmap tracker.",
            "Record and verify lift biomechanics in Form AI before adding load.",
            "Execute the 5-minute dynamic warm-up before lifting any working weight.",
            "Perform evening parasympathetic breathing to accelerate central nervous system recovery."
        ],
        "weeks": weeks_data
    }

    return _enrich_task_ids(roadmap_dict)


# ── Main Generator Pipeline ──────────────────────────────────────────────────

class FitnessRoadmapGenerator:
    """Orchestrates LLM calls across Gemini, Groq, Ollama, with intelligent validation & fallback."""

    async def generate(self, req: RoadmapRequest, user_profile: Dict[str, Any]) -> Tuple[FitnessRoadmapData, str]:
        system_prompt = ROADMAP_SYSTEM_PROMPT
        user_prompt = _build_user_prompt(req, user_profile)
        provider_preference = req.preferred_provider or getattr(settings, "ai_provider", "auto")

        raw_result: Optional[Dict[str, Any]] = None
        provider_used = "engine"

        # 1. Order of providers to try
        providers_to_try: List[str] = []
        if provider_preference == "gemini":
            providers_to_try = ["gemini", "groq", "ollama"]
        elif provider_preference == "groq":
            providers_to_try = ["groq", "gemini", "ollama"]
        elif provider_preference == "ollama":
            providers_to_try = ["ollama", "groq", "gemini"]
        else: # auto
            # Priority: Groq (ultra fast) -> Gemini -> Ollama
            if getattr(settings, "groq_api_key", ""):
                providers_to_try.append("groq")
            if getattr(settings, "gemini_api_key", ""):
                providers_to_try.append("gemini")
            providers_to_try.append("ollama")

        # 2. Try each provider in order
        for p in providers_to_try:
            try:
                if p == "gemini":
                    raw_result = await _call_gemini(system_prompt, user_prompt, settings)
                elif p == "groq":
                    raw_result = await _call_groq(system_prompt, user_prompt, settings)
                elif p == "ollama":
                    raw_result = await _call_ollama(system_prompt, user_prompt, settings)

                if raw_result and "weeks" in raw_result and len(raw_result["weeks"]) > 0:
                    provider_used = p
                    break
            except Exception as ex:
                print(f"[RoadmapGenerator] Provider {p} encountered exception: {ex}")
                continue

        # 3. Fallback to deterministic algorithmic generator if LLM was unreachable or invalid
        if not raw_result or "weeks" not in raw_result or len(raw_result["weeks"]) == 0:
            print("[RoadmapGenerator] Falling back to high-grade deterministic algorithmic generator.")
            raw_result = _generate_deterministic_roadmap(req, user_profile)
            provider_used = "algorithmic_engine"

        # 4. Enrich task IDs for tracking & validate against Pydantic schema
        raw_result = _enrich_task_ids(raw_result)
        validated_roadmap = FitnessRoadmapData(**raw_result)
        
        return validated_roadmap, provider_used
