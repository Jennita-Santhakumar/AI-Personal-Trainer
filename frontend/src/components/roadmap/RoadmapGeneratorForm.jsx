import React, { useState, useEffect } from "react";
import api from "../../services/api";

const T = {
  bg: "#131313",
  surface: "#1c1b1b",
  card: "#201f1f",
  cardHigh: "#2a2a2a",
  primary: "#00d4aa",
  primaryD: "#00b896",
  silver: "#c8c6c6",
  dim: "#888580",
  text: "#e8e6df",
  error: "#ffb4ab",
  success: "#97c459",
  fontD: "'Space Grotesk', sans-serif",
  fontB: "'Lexend', sans-serif",
};

const GOALS = [
  { value: "strength", label: "Max Strength", icon: "🏋️", desc: "Build peak neurological force & heavy compound power" },
  { value: "hypertrophy", label: "Muscle Hypertrophy", icon: "💪", desc: "Maximize muscle protein synthesis & aesthetic volume" },
  { value: "fat_loss", label: "Fat Loss & Definition", icon: "🔥", desc: "Shed visceral & subcutaneous fat while retaining lean mass" },
  { value: "body_recomposition", label: "Body Recomposition", icon: "⚡", desc: "Simultaneously build dense muscle & drop body fat" },
  { value: "endurance", label: "Cardio & Stamina", icon: "🏃", desc: "Boost VO2 Max, mitochondrial density & aerobic threshold" },
  { value: "athletic_performance", label: "Athletic Conditioning", icon: "🎯", desc: "Explosive speed, power, agility, and sports readiness" },
  { value: "flexibility_mobility", label: "Mobility & Longevity", icon: "🧘", desc: "Joint health, range of motion, and posture restoration" },
];

const LEVELS = [
  { value: "beginner", label: "Beginner", desc: "< 1 year structured training, mastering foundational patterns" },
  { value: "intermediate", label: "Intermediate", desc: "1–3 years consistent lifting, comfortable with progressive overload" },
  { value: "advanced", label: "Advanced", desc: "3+ years specialized training, peaking protocols & periodization" },
];

const EQUIPMENTS = [
  { value: "full_gym", label: "Commercial Gym", icon: "🏢", desc: "Barbells, dumbbells, cable stacks, machines, benches" },
  { value: "dumbbells_only", label: "Dumbbells Only", icon: "🏋️", desc: "Adjustable or fixed dumbbells & adjustable bench" },
  { value: "home_gym", label: "Home Garage Gym", icon: "🏠", desc: "Squat rack, Olympic barbell, plates, pull-up bar" },
  { value: "kettlebells", label: "Kettlebell Setup", icon: "🔔", desc: "Pair of kettlebells, resistance bands, bodyweight" },
  { value: "bodyweight", label: "Calisthenics / Bodyweight", icon: "🤸", desc: "Floor, pull-up bar, dip bars, gymnastic rings" },
];

const DIETARY_STYLES = [
  { value: "high_protein", label: "High Protein", icon: "🥩", desc: "2.0-2.4g protein/kg for peak recovery" },
  { value: "balanced", label: "Macro Balanced", icon: "🥑", desc: "40% Carbs, 30% Protein, 30% Healthy Fats" },
  { value: "vegetarian", label: "High-Protein Vegetarian", icon: "🥗", desc: "Dairy, eggs, tofu, tempeh, legumes & plant grains" },
  { value: "vegan", label: "Plant-Based Performance", icon: "🌱", desc: "100% plant-based with complete amino acid profiles" },
  { value: "mediterranean", label: "Mediterranean Longevity", icon: "🫒", desc: "Wild fish, extra virgin olive oil, whole grains, nuts" },
  { value: "keto", label: "Ketogenic / Low-Carb", icon: "🍳", desc: "High healthy fats, moderate protein, <30g net carbs" },
  { value: "paleo", label: "Paleo Archetype", icon: "🥥", desc: "Whole unprocessed meats, berries, root vegetables" },
];

const CALORIE_STRATEGIES = [
  { value: "moderate_deficit", label: "Moderate Deficit (-400 kcal)", desc: "Steady fat loss without muscle catabolism or metabolic slowdown" },
  { value: "aggressive_deficit", label: "Aggressive Cut (-650 kcal)", desc: "Fast fat loss for event readiness or rapid body fat reduction" },
  { value: "maintenance", label: "True Iso-Caloric Maintenance", desc: "Maximum training energy, recovery, and body recomposition" },
  { value: "lean_bulk", label: "Lean Hypertrophic Surplus (+250 kcal)", desc: "Clean muscle accretion with minimal adipose tissue gain" },
  { value: "surplus", label: "Mass Gaining Surplus (+500 kcal)", desc: "Maximal strength and muscular mass accrual" },
];

const INJURIES_LIST = [
  { id: "lower_back", label: "Lower Back / Lumbar" },
  { id: "knee", label: "Knee / Patellar" },
  { id: "shoulder", label: "Shoulder / Rotator Cuff" },
  { id: "wrist", label: "Wrist / Forearm" },
  { id: "neck", label: "Neck / Cervical" },
  { id: "ankle", label: "Ankle / Achilles" },
  { id: "hip", label: "Hip / Femoroacetabular" },
];

const TARGET_FOCUS_OPTIONS = [
  "Upper Chest & Delts", "Posterior Chain (Glutes & Hamstrings)", "Lats & V-Taper Back",
  "Core & Anti-Extension", "Arms (Biceps & Triceps)", "Quadriceps & Squat Strength",
  "Running Speed & Aerobic Base", "Explosive Hip Hinge Power"
];

const LOADING_STAGES = [
  "Synthesizing biometric profile & caloric baselines...",
  "Querying LLM Engine (Gemini / Groq / Ollama)...",
  "Constructing multi-week periodized split & progressive overload...",
  "Formulating micronutrient balance & timing schedules...",
  "Applying biomechanical safety & joint-protective substitutions...",
  "Validating machine-readable JSON schema output...",
];

export default function RoadmapGeneratorForm({ onRoadmapGenerated, onCancel }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    goal: "hypertrophy",
    level: "intermediate",
    weeks: 4,
    days_per_week: 4,
    equipment: "full_gym",
    dietary_preference: "high_protein",
    calorie_preference: "moderate_deficit",
    target_calories: "",
    injuries: [],
    sport_focus: "general",
    target_focus_areas: [],
    preferred_provider: "auto",
  });

  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);
  const [error, setError] = useState("");
  const [providers, setProviders] = useState(null);

  useEffect(() => {
    api.getRoadmapProviders().then(setProviders).catch(() => {});
  }, []);

  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(() => {
        setLoadingStage((prev) => (prev + 1) % LOADING_STAGES.length);
      }, 1600);
    } else {
      setLoadingStage(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const toggleInjury = (id) => {
    setFormData((prev) => ({
      ...prev,
      injuries: prev.injuries.includes(id)
        ? prev.injuries.filter((x) => x !== id)
        : [...prev.injuries, id],
    }));
  };

  const toggleFocusArea = (area) => {
    setFormData((prev) => ({
      ...prev,
      target_focus_areas: prev.target_focus_areas.includes(area)
        ? prev.target_focus_areas.filter((x) => x !== area)
        : [...prev.target_focus_areas, area],
    }));
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = {
        ...formData,
        weeks: parseInt(formData.weeks, 10),
        days_per_week: parseInt(formData.days_per_week, 10),
        target_calories: formData.target_calories ? parseInt(formData.target_calories, 10) : undefined,
      };
      const res = await api.generateRoadmap(payload);
      onRoadmapGenerated?.(res);
    } catch (err) {
      setError(err.message || "Failed to generate roadmap. Please check your settings.");
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => setStep((s) => Math.min(s + 1, 4));
  const prevStep = () => setStep((s) => Math.max(s - 1, 1));

  // Loading Screen
  if (loading) {
    return (
      <div
        style={{
          minHeight: "65vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "3rem 1.5rem",
          textAlign: "center",
        }}
      >
        <div style={{ position: "relative", marginBottom: 30 }}>
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: "50%",
              border: `3px solid rgba(0,212,170,0.15)`,
              borderTopColor: T.primary,
              animation: "spin 0.9s cubic-bezier(0.68, -0.55, 0.27, 1.55) infinite",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              fontSize: 26,
            }}
          >
            ⚡
          </div>
        </div>

        <div
          style={{
            fontFamily: T.fontD,
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.2em",
            color: T.primary,
            textTransform: "uppercase",
            marginBottom: 10,
          }}
        >
          AI INTELLIGENCE PIPELINE
        </div>
        <h3
          style={{
            fontFamily: T.fontD,
            fontSize: "clamp(20px, 3.5vw, 26px)",
            fontWeight: 700,
            color: T.text,
            margin: "0 0 16px",
            letterSpacing: "-0.01em",
          }}
        >
          GENERATING {formData.weeks}-WEEK MASTER ROADMAP
        </h3>

        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            background: "rgba(0, 212, 170, 0.08)",
            border: "1px solid rgba(0, 212, 170, 0.2)",
            padding: "10px 20px",
            borderRadius: 30,
            fontFamily: T.fontB,
            fontSize: 13,
            color: T.primary,
            maxWidth: 500,
            transition: "all 0.3s ease",
          }}
        >
          <span style={{ fontSize: 16 }}>⚙️</span>
          <span>{LOADING_STAGES[loadingStage]}</span>
        </div>

        <div style={{ marginTop: 28, display: "flex", gap: 6 }}>
          {LOADING_STAGES.map((_, i) => (
            <div
              key={i}
              style={{
                width: 24,
                height: 4,
                borderRadius: 2,
                background: i <= loadingStage ? T.primary : "rgba(255,255,255,0.1)",
                transition: "all 0.3s ease",
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  const inp = {
    fontSize: 13,
    padding: "11px 14px",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 10,
    background: T.bg,
    color: T.text,
    width: "100%",
    fontFamily: T.fontB,
    outline: "none",
  };

  const labelStyle = {
    fontFamily: T.fontD,
    fontSize: 9,
    fontWeight: 700,
    letterSpacing: "0.14em",
    textTransform: "uppercase",
    color: T.dim,
    display: "block",
    marginBottom: 8,
  };

  return (
    <div style={{ maxWidth: 840, margin: "0 auto", padding: "20px 24px 48px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28 }}>
        <div>
          <div style={{ fontFamily: T.fontD, fontSize: 10, fontWeight: 700, letterSpacing: "0.2em", color: T.primary, textTransform: "uppercase", marginBottom: 6 }}>
            FULL-STACK ARCHITECTURE
          </div>
          <h2 style={{ fontFamily: T.fontD, fontSize: "clamp(22px, 3.5vw, 30px)", fontWeight: 700, letterSpacing: "-0.02em", color: T.text, margin: 0 }}>
            FITNESS & NUTRITION ROADMAP GENERATOR
          </h2>
          <p style={{ fontFamily: T.fontB, fontSize: 13, color: T.dim, margin: "6px 0 0" }}>
            LLM-engineered multi-week training splits, precision macros, and progressive periodization.
          </p>
        </div>
        {onCancel && (
          <button
            onClick={onCancel}
            style={{
              fontFamily: T.fontD,
              fontSize: 11,
              fontWeight: 700,
              padding: "8px 16px",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,0.1)",
              background: "transparent",
              color: T.dim,
              cursor: "pointer",
            }}
          >
            CANCEL
          </button>
        )}
      </div>

      {/* Step Indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 30 }}>
        {[
          { num: 1, label: "GOALS & TIMELINE" },
          { num: 2, label: "EQUIPMENT & LEVEL" },
          { num: 3, label: "NUTRITION & MACROS" },
          { num: 4, label: "INJURIES & AI MODEL" },
        ].map((s) => {
          const active = step === s.num;
          const done = step > s.num;
          return (
            <div
              key={s.num}
              onClick={() => setStep(s.num)}
              style={{
                flex: 1,
                cursor: "pointer",
                padding: "10px 12px",
                borderRadius: 10,
                background: active ? "rgba(0, 212, 170, 0.08)" : T.surface,
                border: active ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.05)",
                display: "flex",
                alignItems: "center",
                gap: 10,
                transition: "all 0.2s",
              }}
            >
              <div
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  background: done ? T.primary : active ? `linear-gradient(135deg, ${T.primary}, ${T.primaryD})` : "#2a2a2a",
                  color: done || active ? "#131313" : T.dim,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontFamily: T.fontD,
                  fontSize: 11,
                  fontWeight: 700,
                }}
              >
                {done ? "✓" : s.num}
              </div>
              <span
                style={{
                  fontFamily: T.fontD,
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  color: active ? T.primary : done ? T.silver : T.dim,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {s.label}
              </span>
            </div>
          );
        })}
      </div>

      {error && (
        <div
          style={{
            background: "rgba(255, 180, 171, 0.08)",
            border: "1px solid rgba(255, 180, 171, 0.25)",
            borderRadius: 10,
            padding: "12px 16px",
            color: T.error,
            fontFamily: T.fontB,
            fontSize: 13,
            marginBottom: 24,
          }}
        >
          ⚠ {error}
        </div>
      )}

      {/* Step 1: Goals & Timeline */}
      {step === 1 && (
        <div style={{ animation: "fadeUp 0.25s ease" }}>
          <div style={{ marginBottom: 26 }}>
            <label style={labelStyle}>SELECT PRIMARY FITNESS OBJECTIVE</label>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10 }}>
              {GOALS.map((g) => {
                const sel = formData.goal === g.value;
                return (
                  <div
                    key={g.value}
                    onClick={() => setFormData((f) => ({ ...f, goal: g.value }))}
                    style={{
                      padding: "16px 18px",
                      borderRadius: 12,
                      cursor: "pointer",
                      border: sel ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.06)",
                      background: sel ? "rgba(0, 212, 170, 0.07)" : T.surface,
                      transition: "all 0.15s ease",
                      display: "flex",
                      flexDirection: "column",
                      gap: 6,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ fontSize: 20 }}>{g.icon}</span>
                      <span style={{ fontFamily: T.fontD, fontSize: 13, fontWeight: 700, color: sel ? T.primary : T.text }}>
                        {g.label}
                      </span>
                    </div>
                    <div style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim, lineHeight: 1.4 }}>{g.desc}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, background: T.surface, padding: "20px 22px", borderRadius: 14, marginBottom: 24 }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <label style={labelStyle}>PROGRAM LENGTH</label>
                <span style={{ fontFamily: T.fontD, fontSize: 12, fontWeight: 700, color: T.primary }}>
                  {formData.weeks} WEEKS
                </span>
              </div>
              <input
                type="range"
                min={2}
                max={12}
                step={2}
                value={formData.weeks}
                onChange={(e) => setFormData((f) => ({ ...f, weeks: e.target.value }))}
                style={{ width: "100%" }}
              />
              <div style={{ display: "flex", justifyContent: "space-between", fontFamily: T.fontD, fontSize: 9, color: T.dim, marginTop: 6 }}>
                <span>2 WKS (Micro)</span>
                <span>4 WKS (Standard)</span>
                <span>8 WKS (Macro)</span>
                <span>12 WKS (Peaking)</span>
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <label style={labelStyle}>WORKOUT FREQUENCY</label>
                <span style={{ fontFamily: T.fontD, fontSize: 12, fontWeight: 700, color: T.primary }}>
                  {formData.days_per_week} DAYS / WEEK
                </span>
              </div>
              <input
                type="range"
                min={2}
                max={6}
                step={1}
                value={formData.days_per_week}
                onChange={(e) => setFormData((f) => ({ ...f, days_per_week: e.target.value }))}
                style={{ width: "100%" }}
              />
              <div style={{ display: "flex", justifyContent: "space-between", fontFamily: T.fontD, fontSize: 9, color: T.dim, marginTop: 6 }}>
                <span>2 Days (Full Body)</span>
                <span>4 Days (Upper/Lower)</span>
                <span>6 Days (PPL Split)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Experience & Equipment */}
      {step === 2 && (
        <div style={{ animation: "fadeUp 0.25s ease" }}>
          <div style={{ marginBottom: 26 }}>
            <label style={labelStyle}>EXPERIENCE LEVEL</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
              {LEVELS.map((l) => {
                const sel = formData.level === l.value;
                return (
                  <div
                    key={l.value}
                    onClick={() => setFormData((f) => ({ ...f, level: l.value }))}
                    style={{
                      padding: "16px 18px",
                      borderRadius: 12,
                      cursor: "pointer",
                      border: sel ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.06)",
                      background: sel ? "rgba(0, 212, 170, 0.07)" : T.surface,
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div style={{ fontFamily: T.fontD, fontSize: 13, fontWeight: 700, color: sel ? T.primary : T.text, marginBottom: 6 }}>
                      {l.label}
                    </div>
                    <div style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim, lineHeight: 1.4 }}>{l.desc}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ marginBottom: 26 }}>
            <label style={labelStyle}>AVAILABLE TRAINING EQUIPMENT</label>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10 }}>
              {EQUIPMENTS.map((eq) => {
                const sel = formData.equipment === eq.value;
                return (
                  <div
                    key={eq.value}
                    onClick={() => setFormData((f) => ({ ...f, equipment: eq.value }))}
                    style={{
                      padding: "16px",
                      borderRadius: 12,
                      cursor: "pointer",
                      border: sel ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.06)",
                      background: sel ? "rgba(0, 212, 170, 0.07)" : T.surface,
                      transition: "all 0.15s ease",
                      display: "flex",
                      flexDirection: "column",
                      gap: 4,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 18 }}>{eq.icon}</span>
                      <span style={{ fontFamily: T.fontD, fontSize: 12, fontWeight: 700, color: sel ? T.primary : T.text }}>
                        {eq.label}
                      </span>
                    </div>
                    <div style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim, lineHeight: 1.4 }}>{eq.desc}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Nutrition & Macros */}
      {step === 3 && (
        <div style={{ animation: "fadeUp 0.25s ease" }}>
          <div style={{ marginBottom: 26 }}>
            <label style={labelStyle}>DIETARY ARCHETYPE</label>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10 }}>
              {DIETARY_STYLES.map((d) => {
                const sel = formData.dietary_preference === d.value;
                return (
                  <div
                    key={d.value}
                    onClick={() => setFormData((f) => ({ ...f, dietary_preference: d.value }))}
                    style={{
                      padding: "14px 16px",
                      borderRadius: 12,
                      cursor: "pointer",
                      border: sel ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.06)",
                      background: sel ? "rgba(0, 212, 170, 0.07)" : T.surface,
                      transition: "all 0.15s ease",
                      display: "flex",
                      flexDirection: "column",
                      gap: 4,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 18 }}>{d.icon}</span>
                      <span style={{ fontFamily: T.fontD, fontSize: 12, fontWeight: 700, color: sel ? T.primary : T.text }}>
                        {d.label}
                      </span>
                    </div>
                    <div style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim, lineHeight: 1.4 }}>{d.desc}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ marginBottom: 26 }}>
            <label style={labelStyle}>CALORIC DEFICIT / SURPLUS STRATEGY</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8 }}>
              {CALORIE_STRATEGIES.map((c) => {
                const sel = formData.calorie_preference === c.value;
                return (
                  <div
                    key={c.value}
                    onClick={() => setFormData((f) => ({ ...f, calorie_preference: c.value }))}
                    style={{
                      padding: "12px 16px",
                      borderRadius: 10,
                      cursor: "pointer",
                      border: sel ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.05)",
                      background: sel ? "rgba(0, 212, 170, 0.07)" : T.surface,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div>
                      <div style={{ fontFamily: T.fontD, fontSize: 12, fontWeight: 700, color: sel ? T.primary : T.silver }}>
                        {c.label}
                      </div>
                      <div style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim, marginTop: 2 }}>{c.desc}</div>
                    </div>
                    <div style={{ width: 16, height: 16, borderRadius: "50%", border: sel ? `4px solid ${T.primary}` : "2px solid #555" }} />
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ background: T.surface, padding: "16px 20px", borderRadius: 12 }}>
            <label style={labelStyle}>CUSTOM DAILY CALORIC TARGET (OPTIONAL OVERRIDE)</label>
            <input
              type="number"
              placeholder="e.g. 2400 (Leave blank for automated BMR/TDEE calculation)"
              value={formData.target_calories}
              onChange={(e) => setFormData((f) => ({ ...f, target_calories: e.target.value }))}
              style={inp}
            />
          </div>
        </div>
      )}

      {/* Step 4: Injuries, Focus & AI Engine */}
      {step === 4 && (
        <div style={{ animation: "fadeUp 0.25s ease" }}>
          <div style={{ marginBottom: 26 }}>
            <label style={labelStyle}>INJURY HISTORY & CONTRAINDICATIONS (SELECT ALL THAT APPLY)</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {INJURIES_LIST.map((inj) => {
                const sel = formData.injuries.includes(inj.id);
                return (
                  <button
                    type="button"
                    key={inj.id}
                    onClick={() => toggleInjury(inj.id)}
                    style={{
                      padding: "8px 16px",
                      borderRadius: 20,
                      fontFamily: T.fontD,
                      fontSize: 11,
                      fontWeight: 700,
                      letterSpacing: "0.06em",
                      cursor: "pointer",
                      border: sel ? `1px solid ${T.error}` : "1px solid rgba(255,255,255,0.08)",
                      background: sel ? "rgba(255, 180, 171, 0.12)" : T.surface,
                      color: sel ? T.error : T.silver,
                      transition: "all 0.15s ease",
                    }}
                  >
                    {sel ? "⚠️ " : "+ "}
                    {inj.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div style={{ marginBottom: 26 }}>
            <label style={labelStyle}>TARGET FOCUS AREAS / PRIORITY MUSCLE GROUPS</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {TARGET_FOCUS_OPTIONS.map((area) => {
                const sel = formData.target_focus_areas.includes(area);
                return (
                  <button
                    type="button"
                    key={area}
                    onClick={() => toggleFocusArea(area)}
                    style={{
                      padding: "8px 16px",
                      borderRadius: 20,
                      fontFamily: T.fontD,
                      fontSize: 11,
                      fontWeight: 700,
                      letterSpacing: "0.06em",
                      cursor: "pointer",
                      border: sel ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.08)",
                      background: sel ? "rgba(0, 212, 170, 0.1)" : T.surface,
                      color: sel ? T.primary : T.silver,
                      transition: "all 0.15s ease",
                    }}
                  >
                    {sel ? "✓ " : "+ "}
                    {area}
                  </button>
                );
              })}
            </div>
          </div>

          <div style={{ background: T.surface, padding: "20px 22px", borderRadius: 14, marginBottom: 20 }}>
            <label style={labelStyle}>AI INFERENCE PROVIDER ENGINE</label>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 8, marginTop: 10 }}>
              {[
                { id: "auto", label: "AUTO (Recommended)", icon: "✨", desc: "Fastest available (Groq / Gemini / Ollama)" },
                { id: "gemini", label: "Google Gemini", icon: "💎", desc: providers?.gemini?.available ? "Online (1.5 Flash)" : "API Key Required" },
                { id: "groq", label: "Groq LPU", icon: "⚡", desc: providers?.groq?.available ? "Online (Llama 3.3)" : "API Key Required" },
                { id: "ollama", label: "Local Ollama", icon: "🦙", desc: providers?.ollama?.available ? "Docker / Local" : "Local Daemon" },
              ].map((p) => {
                const sel = formData.preferred_provider === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => setFormData((f) => ({ ...f, preferred_provider: p.id }))}
                    style={{
                      padding: "12px 14px",
                      borderRadius: 10,
                      cursor: "pointer",
                      border: sel ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.06)",
                      background: sel ? "rgba(0, 212, 170, 0.08)" : T.bg,
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                      <span>{p.icon}</span>
                      <span style={{ fontFamily: T.fontD, fontSize: 11, fontWeight: 700, color: sel ? T.primary : T.text }}>
                        {p.label}
                      </span>
                    </div>
                    <div style={{ fontFamily: T.fontB, fontSize: 10, color: T.dim }}>{p.desc}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Navigation Buttons */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 32, paddingTop: 20, borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        {step > 1 ? (
          <button
            type="button"
            onClick={prevStep}
            style={{
              padding: "12px 24px",
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.1)",
              background: "transparent",
              color: T.silver,
              fontFamily: T.fontD,
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.1em",
              cursor: "pointer",
              textTransform: "uppercase",
            }}
          >
            ← BACK
          </button>
        ) : (
          <div />
        )}

        {step < 4 ? (
          <button
            type="button"
            onClick={nextStep}
            style={{
              padding: "13px 32px",
              borderRadius: 10,
              border: "none",
              background: `linear-gradient(135deg, ${T.primary}, ${T.primaryD})`,
              color: "#131313",
              fontFamily: T.fontD,
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: "0.1em",
              cursor: "pointer",
              textTransform: "uppercase",
              boxShadow: "0 4px 20px rgba(0, 212, 170, 0.25)",
            }}
          >
            CONTINUE →
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            style={{
              padding: "14px 38px",
              borderRadius: 10,
              border: "none",
              background: `linear-gradient(135deg, ${T.primary}, ${T.primaryD})`,
              color: "#131313",
              fontFamily: T.fontD,
              fontSize: 13,
              fontWeight: 700,
              letterSpacing: "0.1em",
              cursor: "pointer",
              textTransform: "uppercase",
              boxShadow: "0 4px 24px rgba(0, 212, 170, 0.35)",
            }}
          >
            ⚡ GENERATE AI ROADMAP
          </button>
        )}
      </div>
    </div>
  );
}
