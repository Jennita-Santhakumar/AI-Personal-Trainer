"""
features/coach/prompts.py — all prompt templates for the AI coach.
"""

SYSTEM_PROMPT = """You are an elite personal fitness coach with deep expertise in:
- Powerlifting (SBD competition, programming, peaking)
- Running (5k to marathon, speed development, endurance)
- Swimming (technique, open water, stamina)
- Yoga (flexibility, breathwork, recovery protocols)
- Injury prevention and rehabilitation

Your coaching philosophy:
1. Evidence-based training principles before bro-science
2. Technique and safety always before intensity
3. Progressive overload — sustainable, not reckless
4. Recovery IS training — sleep, nutrition, and stress management matter
5. Adapt to the individual — cookie-cutter programmes are a last resort
6. Never fabricate data or statistics — if uncertain, say so

Tone: Direct, warm, specific. Avoid vague praise. When you say "good job", name exactly what was good.
When suggesting changes, explain the physiological WHY — the user should understand their own body.
"""

USER_CONTEXT_TEMPLATE = """\
== User profile ==
Name: {name}
Goal: {goal} | Level: {level}
Program week: {week} | Streak: {streak} days
Injuries / limitations: {injuries}

== Personal records ==
{prs}

== Last {n_recent} sessions ==
{recent_sessions}

== Recurring form issues (last 10 sessions) ==
{form_issues}

== Average rep quality (last 5 sessions) ==
{avg_quality}

== Today's completed session ==
{todays_session}

== Relevant past coaching (semantic recall) ==
{past_advice}
"""

TEMPLATES = {
    "post_session": """\
The user just completed: {activity}
Reps: {reps} | Weight: {weight}
Form violations: {violations}
Quality score: {quality}
Self-reported RPE: {rpe}/10

Respond in this structure:
1. WHAT WENT WELL (specific — reference quality score and any clean patterns)
2. PRIORITY FIX (one thing only — most impactful correction)
3. NEXT SESSION CUES (two specific technical cues)
4. LOAD DECISION (add weight / hold / reduce — with physiological reason)

Under 150 words. Direct, not vague.""",

    "plateau_diagnosis": """\
The user has not improved {lift} in {weeks} weeks.
Recent data: {session_summary}
Injuries: {injuries}

Diagnose the plateau considering in order:
1. Technique inefficiency (most common)
2. Recovery deficit (sleep, food, stress)
3. Programming error (volume, intensity, frequency)
4. Need for variation

Name the most likely cause from their data.
Prescribe ONE specific intervention with exact exercises, sets, reps, or protocol.""",

    "injury_prevention_alert": """\
Form correction system flagged: {pattern}
Detected in {count} of last {sessions} sessions
Affected area: {area}

Respond:
1. Why this pattern is problematic (anatomy + mechanics — 2 sentences)
2. Specific injury risk if uncorrected
3. Three corrective exercises (name, sets, reps)
4. Load recommendation: reduce / hold / continue (+ reason)""",

    "weekly_review": """\
Week {week} for {name}:
Sessions: {completed}/{planned} | Avg quality: {avg_quality}
PRs: {prs} | Calories: {calories} | Streak: {streak} days

Write a 100-word weekly review:
1. Top achievement (specific)
2. One thing to improve next week (specific)
3. Intensity recommendation based on fatigue signals
4. One motivating statement tied to their goal: {goal}""",

    "adaptive_plan": """\
{name} reported: {reason}
Planned session: {planned_session}
Form quality trend: {trend}

Decide and explain:
- PROCEED: Safe to continue as planned (explain why)
- MODIFY: Adjust today (provide exact alternative: exercises, sets, reps, intensity)
- REST: Recommend full rest (physiological reason)""",

    "technique_explainer": """\
User question: "{question}"
Level: {level} | Current form issues: {form_issues}

Explain with:
1. Biomechanical reason it matters (no jargon)
2. Simple self-check using a phone camera
3. One drill to groove the pattern (name, sets, reps)
4. Common mistake to avoid

Use an analogy if helpful. Practical, not academic.""",

    "daily_briefing": """\
Generate a morning briefing for {name}.
Week {week} of their program. Last session: {last_session}.
Streak: {streak} days. Common form issues: {form_issues}.

Include:
1. What to focus on today (specific and actionable)
2. One technique cue based on recent form data
3. Recovery note if streak >= 4 days
4. One motivating line — specific to their goal, not generic

Under 120 words. Second person ("you"). Energising, not generic.""",

    "injury_risk_advice": """\
Risk signals detected for {name}:
{signals}

For each signal:
1. Explain the mechanism simply
2. Give ONE concrete action to reduce risk
3. Flag if they should pause training

Be direct — do not minimise real risks.""",
}
