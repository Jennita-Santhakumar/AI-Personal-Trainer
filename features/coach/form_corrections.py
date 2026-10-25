"""
features/coach/form_corrections.py

Comprehensive form correction database for ALL major workout categories.
Each exercise has:
  - cues: what to focus on (coaching cues)
  - common_mistakes: what goes wrong and WHY
  - fixes: specific drills or adjustments
  - injury_risks: what breaks if ignored
  - self_check: how to verify with a phone camera
"""

FORM_CORRECTIONS = {

    # ── POWERLIFTING / BARBELL ────────────────────────────────────────────────

    "squat": {
        "cues": [
            "Chest up, proud chest throughout the whole rep",
            "Knees track over toes — push them OUT",
            "Drive the floor away — don't think 'stand up', think 'leg press the earth'",
            "Big breath into your belly before you descend, brace hard",
            "Break at hips and knees simultaneously",
        ],
        "common_mistakes": [
            {"mistake": "Knee cave (valgus collapse)", "why": "Weak glutes + adductors let knees track inward under load", "fix": "Banded squats — put a band just above knees, actively push against it every rep"},
            {"mistake": "Forward torso lean / 'good morning squat'", "why": "Weak upper back or tight ankles shifting load forward", "fix": "Box squat to learn hip hinge, goblet squat to groove upright torso"},
            {"mistake": "Heels rising", "why": "Ankle dorsiflexion restriction", "fix": "Elevate heels 1–2cm on plates while you work on ankle mobility (3x10 ankle circles + calf stretches daily)"},
            {"mistake": "Butt wink (posterior pelvic tilt at bottom)", "why": "Hip mobility limitation or going beyond depth capability", "fix": "Find your 'natural depth' — just above where butt wink starts. Work hip 90/90 stretches daily"},
            {"mistake": "Bar rolling up the neck", "why": "Bar placed too high, no shelf created", "fix": "Retract scapulae hard — create a muscle shelf. Bar sits on traps, not the bones"},
        ],
        "injury_risks": ["Knee ligament stress from valgus", "Lower back from forward lean", "SI joint from excessive butt wink"],
        "self_check": "Film from the side at knee height. Watch: depth (hip crease below knee), torso angle, heel contact. Film from front: knee tracking over second toe.",
        "warmup_drills": ["Bodyweight squat x15", "Goblet squat x10", "Band pull-apart x15", "Hip 90/90 x60s each side"],
    },

    "bench": {
        "cues": [
            "Arch your back — get your chest UP to the bar, not bar down to chest",
            "Shoulder blades pinched and TUCKED down into the bench — never let them wing",
            "Bar path: touch lower chest, press back and slightly toward face (diagonal)",
            "Leg drive — push feet into the floor, drive hips into bench",
            "Grip: wrists straight, bar in the heel of palm not fingers",
        ],
        "common_mistakes": [
            {"mistake": "Wrists bent back", "why": "Puts load on wrist joint, not the palm/bones", "fix": "Wrap wrists OR consciously push heel of hand into bar. Bar should sit directly over wrist bones"},
            {"mistake": "Flared elbows at 90°", "why": "Destroys shoulder health — impingement + rotator cuff stress", "fix": "45–60° elbow flare. Think 'bend the bar in half' to engage lats as a shelf"},
            {"mistake": "Bouncing bar off chest", "why": "Momentum replaces pec strength, risks sternum bruising", "fix": "1 second pause at chest. If you can't lift it from a dead pause, the weight is too heavy"},
            {"mistake": "Butt comes off bench", "why": "Using hip extension to cheat the sticking point", "fix": "Intentional — powerlifting allows arch but butt must stay down. In raw lifting, reduce weight"},
            {"mistake": "Uneven bar path / one arm leading", "why": "Side-to-side strength imbalance", "fix": "Dumbbell bench press 3x10 to force each arm to work independently"},
        ],
        "injury_risks": ["Rotator cuff tear from flared elbows", "Pec tear from over-stretching at bottom", "Wrist tendinopathy"],
        "self_check": "Film from the side at bench level. Check: bar touches lower chest not neck, forearms vertical at bottom, back arch consistent.",
        "warmup_drills": ["Band pull-apart x20", "Face pull x15", "Rotator cuff external rotation x12", "Empty bar x10 paused"],
    },

    "deadlift": {
        "cues": [
            "Lat engagement first: 'protect your armpits' — squeeze as if holding oranges under your arms",
            "Push the floor away to initiate — don't PULL, PUSH",
            "Bar stays in contact with legs the whole way — drag it up your shins",
            "Hips and shoulders rise at the same rate off the floor",
            "Lock out: squeeze glutes, push hips through — don't hyperextend lower back",
        ],
        "common_mistakes": [
            {"mistake": "Rounded lower back", "why": "Spinal erectors overloaded, disc compression risk", "fix": "Reduce weight immediately. Brace: big breath, 360° expansion, then initiate. Practice RDL to learn neutral spine hinge"},
            {"mistake": "Bar drifting away from body", "why": "Lat disengagement — massive mechanical disadvantage", "fix": "Mental cue: 'scrape the bar up your shins'. Wear long socks if helpful"},
            {"mistake": "Hips shooting up first (stripper pull)", "why": "Quad weakness — converting deadlift into a back exercise", "fix": "Pause deadlifts at the knee. Romanian deadlifts for hip hinge strength"},
            {"mistake": "Jerking the bar", "why": "Slack in the bar + trying to yank weight up — back shock loading", "fix": "Take the slack out first: pull bar gently until you feel tension, THEN drive"},
            {"mistake": "Hyperextending at lockout", "why": "Lumbar compression at end range", "fix": "Lock out means: glutes squeezed, standing tall — not leaning back"},
        ],
        "injury_risks": ["Disc herniation from rounded lumbar", "Hamstring tear from bar drift", "Bicep tear from supinated grip with rounded back"],
        "self_check": "Film from the side. Bar over mid-foot at setup. Shins vertical. Watch: hips and shoulders move at same rate. Bar stays against legs.",
        "warmup_drills": ["Cat-cow x10", "Hip hinge with dowel x10", "Romanian deadlift with light bar x10", "Glute bridge x15"],
    },

    "overhead_press": {
        "cues": [
            "Start: bar on front delts, elbows slightly in front of bar (not pointing straight out)",
            "Press: as bar clears forehead, push head THROUGH — finish with bar over ears, not in front",
            "Squeeze glutes and brace abs throughout — no lower back arch",
            "At top: active shoulder — shrug up slightly to pack the joint",
        ],
        "common_mistakes": [
            {"mistake": "Excessive lower back arch", "why": "Core not braced — load transferred to lumbar spine", "fix": "Glute squeeze + ab brace BEFORE unracking. If still arching, reduce weight"},
            {"mistake": "Bar pressed forward in an arc (not straight)", "why": "Inefficient bar path, anterior shoulder overloaded", "fix": "Practice with a wall 5cm in front of you — forces vertical bar path"},
            {"mistake": "Wrists bent back", "why": "Same as bench — wrist joint loaded instead of skeleton", "fix": "Rotate wrists so knuckles point toward ceiling, or use a false grip"},
        ],
        "injury_risks": ["Shoulder impingement", "Rotator cuff strain", "Lower back compression"],
        "self_check": "Film from the side. Bar should travel in a vertical line. At lockout bar is directly over shoulder joint.",
        "warmup_drills": ["Band pull-apart x20", "Face pull x15", "Shoulder dislocate with band x10", "Empty bar press x10"],
    },

    "row": {
        "cues": [
            "Lead with the elbow, not the hand — 'pull elbow to hip pocket'",
            "Chest up, slight arch — don't round forward under load",
            "Full stretch at the bottom — let the scapula protract",
            "Squeeze the retraction at the top, hold 1 second",
        ],
        "common_mistakes": [
            {"mistake": "Using momentum / body swing", "why": "Momentum removes load from target muscles", "fix": "Pause 1 second at top, 1 second at bottom. If you can't — reduce weight"},
            {"mistake": "Elbows flare wide", "why": "Shifts to rear delt instead of lat/rhomboid", "fix": "Keep elbows at ~45° from torso for balanced back development"},
            {"mistake": "Rounding lower back on barbell rows", "why": "Spinal loading at flexion", "fix": "Elevate torso to 45° if mobility limited. Or switch to chest-supported rows"},
        ],
        "injury_risks": ["Bicep tendinopathy from poor elbow path", "Lumbar strain on barbell row"],
        "self_check": "Film from the side. Torso angle consistent, no swing.",
        "warmup_drills": ["Band pull-apart x20", "Face pull x15", "Cat-cow x10"],
    },

    "pull_up": {
        "cues": [
            "Start from DEAD HANG — full shoulder extension, scapulae elevated",
            "Initiate: pull scapulae DOWN and BACK first, then elbows follow",
            "Drive elbows to hips — not pulling with hands",
            "Chin clears bar — don't crane neck to fake the rep",
            "Controlled lower — 2–3 seconds descent",
        ],
        "common_mistakes": [
            {"mistake": "Kipping without strength base", "why": "Shoulder joint stress at end range with momentum", "fix": "Build 5 strict pull-ups before kipping. Negatives: jump to top, lower for 5 seconds"},
            {"mistake": "Partial range (not reaching dead hang)", "why": "Removes lat stretch, reduces strength development", "fix": "Use a box to step down to full hang. Dead hangs 3x30s as mobility work"},
            {"mistake": "Shrugging at bottom", "why": "Traps doing the work instead of lats initiating", "fix": "'Proud chest' at the hang. Practise scapular pull-ups — just retract/depress without bending elbows"},
        ],
        "injury_risks": ["Shoulder impingement from kipping", "Bicep tendon strain"],
        "self_check": "Film from the side. Full hang at bottom, chin over bar at top, no swing.",
        "warmup_drills": ["Dead hang x30s", "Scapular pull-ups x10", "Band-assisted pull-up x5 slow negatives"],
    },

    # ── RUNNING ───────────────────────────────────────────────────────────────

    "running": {
        "cues": [
            "Land midfoot under your hip, not heel-striking out in front",
            "Cadence: aim for 170–180 steps/min — shorter, quicker steps reduce impact",
            "Arms at 90°, hands relaxed (imagine holding crisps without crushing them)",
            "Slight forward lean from ANKLES, not waist",
            "Eyes on the horizon, not down at your feet",
        ],
        "common_mistakes": [
            {"mistake": "Heel striking", "why": "Braking force with every step — knee stress, slower pace", "fix": "Increase cadence by 5–10% — natural consequence is midfoot landing. Metronome app at 175bpm"},
            {"mistake": "Overstriding", "why": "Foot lands far in front of body — braking + hip flexor overload", "fix": "Shorten stride, increase turnover. Run with high knees for 30s, then return to normal pace"},
            {"mistake": "Head down, hunching forward", "why": "Reduces lung capacity, creates neck/shoulder tension", "fix": "Look 10–15m ahead. Monthly form video from the side — watch posture"},
            {"mistake": "Crossover gait (feet crossing midline)", "why": "IT band stress, hip drop, inefficiency", "fix": "Run along a white line — feet should land either side of it, not crossing over"},
            {"mistake": "Too much too soon", "why": "Soft tissue (tendons) adapt 3–4x slower than cardiovascular fitness", "fix": "10% rule: increase weekly mileage by max 10% per week"},
        ],
        "injury_risks": ["Shin splints", "IT band syndrome", "Patellofemoral pain", "Plantar fasciitis", "Stress fractures"],
        "self_check": "Film yourself running from the side and behind. Side: check forward lean, foot landing under hip. Back: check hip drop, crossover.",
        "warmup_drills": ["Leg swing x10 each", "Hip circle x10", "High knees x20m", "Butt kicks x20m", "Dynamic calf raise x10"],
    },

    "easy_run": {
        "cues": ["Conversational pace — you should be able to speak in full sentences", "Nasal breathing if possible", "Relaxed shoulders, arms, hands"],
        "common_mistakes": [
            {"mistake": "Running easy runs too hard", "why": "Defeats recovery purpose — sympathetic nervous system stays activated", "fix": "Use HR: should be 60–70% max HR. If you can't talk, slow down"},
        ],
        "injury_risks": ["Overtraining syndrome from chronically elevated intensity"],
        "self_check": "Can you hold a conversation? If no, too fast.",
        "warmup_drills": ["5 min walk before starting"],
    },

    "hiit": {
        "cues": [
            "Work intervals: genuine maximum effort — rate of perceived exertion 9–10",
            "Rest intervals: active recovery, NOT sitting down",
            "Maintain form even when fatigued — reduce weight before form breaks",
            "Breathe: exhale on exertion, never hold your breath",
        ],
        "common_mistakes": [
            {"mistake": "Work intervals not actually intense", "why": "HIIT benefits come from high metabolic demand — moderate effort is just cardio", "fix": "Track HR: should hit 85–95% max HR in work intervals"},
            {"mistake": "Insufficient rest between sets", "why": "Can't achieve true max effort if not recovered — becomes moderate cardio", "fix": "For true HIIT: work:rest ratio of 1:2 minimum (e.g. 20s on, 40s off)"},
            {"mistake": "Too many HIIT sessions per week", "why": "CNS fatigue, cortisol elevation, injury risk", "fix": "2–3 sessions maximum per week. Need 48h between sessions"},
        ],
        "injury_risks": ["Overuse injuries", "CNS burnout", "Rhabdomyolysis in extreme cases"],
        "self_check": "Are you genuinely unable to speak during work intervals? Good. Can you speak normally within 30s of rest ending? Good.",
        "warmup_drills": ["5 min light cardio", "Dynamic stretching", "2 practice rounds at 50% effort"],
    },

    # ── CYCLING ───────────────────────────────────────────────────────────────

    "cycling": {
        "cues": [
            "Pedal in circles — think of scraping mud off your shoe at the bottom",
            "Soft elbows, relaxed grip — don't white-knuckle the bars",
            "Engage core: don't rock side to side on the saddle",
            "Knee tracks over the pedal spindle — not inside or outside",
        ],
        "common_mistakes": [
            {"mistake": "Saddle too low", "why": "Knee flexion exceeds 90° at bottom — patellofemoral stress, reduced power", "fix": "Saddle height: slight bend in knee at full extension (25–35° flexion at bottom)"},
            {"mistake": "Mashing big gears", "why": "High force, low cadence — knee joint stress", "fix": "Target cadence: 80–100rpm. Use easier gear, higher cadence"},
            {"mistake": "Cleat misalignment", "why": "Knee tracking issues if cleats rotated wrong", "fix": "Natural foot angle when dangling legs off a table = your cleat angle"},
        ],
        "injury_risks": ["Patellofemoral syndrome", "IT band syndrome", "Lower back from bad saddle height", "Achilles from saddle too low"],
        "self_check": "Film from behind: watch for hip rock. From the side: knee at bottom of pedal stroke should have slight bend.",
        "warmup_drills": ["5 min easy spinning", "Leg swings x10", "Hip circles x10"],
    },

    # ── YOGA / FLEXIBILITY ────────────────────────────────────────────────────

    "yoga": {
        "cues": [
            "Breathe into the pose — each exhale allows slightly more depth",
            "Never push past sharp pain — sensation and sharp pain are different",
            "Engage the muscles you're NOT stretching to protect joints",
            "Quality over depth — a shallow pose with control beats a deep pose with collapse",
        ],
        "common_mistakes": [
            {"mistake": "Forcing depth through pain", "why": "Overstretching ligaments — takes months to heal", "fix": "Breathe and find 70% of your range. Let the breath create more space"},
            {"mistake": "Holding breath in difficult poses", "why": "Increases tension, reduces mobility gains, elevates blood pressure", "fix": "If you can't breathe normally in a pose, come out slightly"},
            {"mistake": "Locking joints (hyperextending elbows/knees)", "why": "Passive joint stress — no muscular engagement protecting the joint", "fix": "Micro-bend in all joints. 'Soft knees' in standing poses"},
        ],
        "injury_risks": ["SI joint strain from aggressive forward folds", "Hamstring attachment injuries", "Wrist compression in weight-bearing poses"],
        "self_check": "Can you breathe normally and maintain the pose? If not, reduce intensity.",
        "warmup_drills": ["Cat-cow x10", "Child's pose x60s", "Sun salutation A x3 at slow pace"],
    },

    # ── SWIMMING ─────────────────────────────────────────────────────────────

    "swimming": {
        "cues": [
            "Freestyle: one goggle in water during breathing — don't lift your whole head",
            "High elbow catch — elbow higher than wrist, wrist higher than fingers at entry",
            "Rotate body as a unit — hips follow shoulders",
            "Kick from the hip, not the knee — legs are propulsion + balance, not the engine",
        ],
        "common_mistakes": [
            {"mistake": "Lifting head to breathe", "why": "Hips sink, creates drag, neck strain", "fix": "Rotate body — ear stays in water, one goggle submerged"},
            {"mistake": "Crossing over on entry (hand crossing centerline)", "why": "Creates fishtail, inefficiency, shoulder impingement risk", "fix": "Imagine a line down the middle — each hand enters slightly outside shoulder width"},
            {"mistake": "Bent knee kick", "why": "Creates drag instead of propulsion", "fix": "Kick initiates from hip flexors, knees only slightly bent"},
        ],
        "injury_risks": ["Swimmer's shoulder (rotator cuff impingement)", "Knee pain from breaststroke kick"],
        "self_check": "Underwater camera if available. Watch entry, catch, and breathing rotation.",
        "warmup_drills": ["200m easy drill work", "Kick drills x2 lengths", "Single-arm drill x2 lengths"],
    },

    # ── BODYWEIGHT / CALISTHENICS ─────────────────────────────────────────────

    "push_up": {
        "cues": [
            "Body forms a straight line head to heels — no sagging hips or piked bum",
            "Hands slightly wider than shoulders, fingers pointing forward",
            "Lower until chest grazes floor — full range",
            "Elbows at 45° from body — not flared at 90°, not glued to ribs",
            "Screw hands into floor (imagine rotating them outward) — engages lats, protects shoulders",
        ],
        "common_mistakes": [
            {"mistake": "Hips sagging", "why": "Core not engaged — lower back compression", "fix": "Squeeze glutes and brace abs before every rep. If still sagging — do knee push-ups to build base"},
            {"mistake": "Partial range", "why": "Reduces pec activation at the bottom stretch", "fix": "Lower until chest touches floor, every rep. Better 5 full reps than 20 partial"},
            {"mistake": "Head dropping forward", "why": "Neck strain, compensatory movement", "fix": "Keep eyes fixed on a spot on the floor 30cm ahead"},
        ],
        "injury_risks": ["Shoulder impingement from wide elbows", "Wrist compression"],
        "self_check": "Film from the side: straight body line, chest to floor.",
        "warmup_drills": ["Shoulder circle x10", "Wrist circle x10", "Scapular push-up x10"],
    },

    "plank": {
        "cues": [
            "Forearms parallel, elbows under shoulders",
            "Push the floor away — don't just hang in the position",
            "Squeeze glutes and quads — total body tension",
            "Neutral neck: eyes down, head in line with spine",
        ],
        "common_mistakes": [
            {"mistake": "Hips too high", "why": "Takes load off core, becomes a rest position", "fix": "Have someone tap your hips down, or film yourself"},
            {"mistake": "Holding breath", "why": "Reduces endurance, elevates blood pressure unnecessarily", "fix": "Breathe steadily. If you can't breathe, you've exceeded capacity — rest"},
        ],
        "injury_risks": ["Lower back pain from poor alignment"],
        "self_check": "Film from the side: straight line from head to heels.",
        "warmup_drills": ["Cat-cow x10", "Glute bridge x15"],
    },

    "lunge": {
        "cues": [
            "Vertical front shin — knee tracks over second toe",
            "Back knee drops straight down — not behind you",
            "Upright torso throughout",
            "Drive through front heel to stand",
        ],
        "common_mistakes": [
            {"mistake": "Front knee caving in", "why": "Glute weakness — same as knee cave in squat", "fix": "Think 'push knee out over pinky toe'. Banded lunges"},
            {"mistake": "Knee goes past toes aggressively", "why": "Patellofemoral stress under load", "fix": "Step further forward. Vertical shin is the goal"},
            {"mistake": "Leaning forward", "why": "Quad overloading, glutes switched off", "fix": "Hold a broomstick vertically at your side — it should stay vertical throughout"},
        ],
        "injury_risks": ["Patellar tendinopathy", "Hip flexor strain"],
        "self_check": "Film from the front: knee tracking. From the side: shin angle and torso position.",
        "warmup_drills": ["Hip flexor stretch x30s each", "Glute activation x15", "Bodyweight lunge x10"],
    },

    # ── OLYMPIC / FUNCTIONAL ──────────────────────────────────────────────────

    "clean": {
        "cues": [
            "First pull is SLOW and controlled — don't rip it off the floor",
            "Hips and shoulders rise at the same rate (same as deadlift)",
            "Second pull: when bar passes knees, aggressively extend hips — this is the power",
            "Pull yourself UNDER the bar — don't muscle it up",
            "Catch in a front rack: elbows high and through, bar resting on shoulders",
        ],
        "common_mistakes": [
            {"mistake": "Pulling with arms too early", "why": "Arms should be straight cables until triple extension", "fix": "Think 'jump and shrug' — arms only bend AFTER hips and knees are fully extended"},
            {"mistake": "Bar drifting away from body", "why": "Creates a longer arc — inefficient and slower", "fix": "Bar should graze thighs on the way up"},
        ],
        "injury_risks": ["Wrist injury from poor front rack", "Lower back from early arm pull"],
        "self_check": "Film from the side. Watch: bar path (should be nearly vertical), hip extension timing.",
        "warmup_drills": ["Romanian deadlift x5", "Hang shrug x5", "Front squat x5", "Hang power clean x3 light"],
    },

    "kettlebell_swing": {
        "cues": [
            "Hip HINGE, not a squat — the bell swings from between the legs, not from a squat",
            "Snap hips forward aggressively at the top — glutes do the work",
            "Soft knees, not bent knees",
            "At top: body forms a straight line — don't lean back",
            "Bell is pulled back between legs like a hiking a football — latissimus controls descent",
        ],
        "common_mistakes": [
            {"mistake": "Squatting the swing", "why": "Quad-dominant — misses glute power, fatigues quickly", "fix": "Think hinge: chest goes forward, hips go back"},
            {"mistake": "Arm-muscling the bell up", "why": "Should be hip power, not shoulder work", "fix": "If your arms are working hard, hips aren't — more aggressive hip snap"},
            {"mistake": "Letting bell crash down passively", "why": "Lower back absorbs impact", "fix": "Own the descent — lat tension pulls the bell back into the hinge"},
        ],
        "injury_risks": ["Lower back strain from squatting pattern", "Shoulder injury from muscling"],
        "self_check": "Film from the side. Watch: hip hinge vs squat pattern, shoulder position at top.",
        "warmup_drills": ["Hip hinge with dowel x10", "Glute bridge x15", "Romanian deadlift x10", "Light swing x10"],
    },
}


def get_form_correction(activity: str) -> dict:
    """Return form correction data for a given activity. Fuzzy match common aliases."""
    activity = activity.lower().strip()
    aliases = {
        "bench_press": "bench",
        "bench press": "bench",
        "barbell squat": "squat",
        "back squat": "squat",
        "front squat": "squat",
        "conventional deadlift": "deadlift",
        "sumo deadlift": "deadlift",
        "ohp": "overhead_press",
        "shoulder press": "overhead_press",
        "pull up": "pull_up",
        "chin up": "pull_up",
        "chinup": "pull_up",
        "pushup": "push_up",
        "push up": "push_up",
        "kb swing": "kettlebell_swing",
        "swing": "kettlebell_swing",
        "power clean": "clean",
        "hang clean": "clean",
        "run": "running",
        "jog": "running",
        "interval": "hiit",
        "interval training": "hiit",
    }
    key = aliases.get(activity, activity)
    return FORM_CORRECTIONS.get(key, None)


def get_all_activities() -> list:
    return sorted(FORM_CORRECTIONS.keys())
