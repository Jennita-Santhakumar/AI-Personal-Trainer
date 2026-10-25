import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
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
  info: "#85b7eb",
  warning: "#f5a623",
  fontD: "'Space Grotesk', sans-serif",
  fontB: "'Lexend', sans-serif",
};

export default function RoadmapViewer({
  roadmapData,
  progress = {},
  onProgressChange,
  onRegenerate,
  onSwitchRoadmap,
  history = [],
}) {
  const navigate = useNavigate();
  const [selectedWeekIdx, setSelectedWeekIdx] = useState(0);
  const [activeTab, setActiveTab] = useState("workouts"); // 'workouts' | 'nutrition' | 'milestones' | 'recovery'
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [localProgress, setLocalProgress] = useState(progress);

  const roadmap = roadmapData?.roadmap || roadmapData || {};
  const weeks = roadmap.weeks || [];
  const currentWeek = weeks[selectedWeekIdx] || weeks[0] || {};
  const targetMacros = roadmap.target_macros || {
    calories: 2200,
    protein_g: 160,
    carbs_g: 220,
    fat_g: 65,
    hydration_liters: 3.2,
  };

  // Calculate total and completed tasks
  let totalTasks = 0;
  let completedTasks = 0;
  weeks.forEach((w) => {
    (w.workout_days || []).forEach((d) => {
      (d.exercises || []).forEach((ex) => {
        totalTasks++;
        if (localProgress[ex.id]) completedTasks++;
      });
    });
    (w.milestones || []).forEach((m) => {
      totalTasks++;
      if (localProgress[m.id]) completedTasks++;
    });
  });

  const completionPercentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const handleToggleTask = async (taskId) => {
    const isDone = !localProgress[taskId];
    const updated = { ...localProgress, [taskId]: isDone };
    if (!isDone) delete updated[taskId];
    setLocalProgress(updated);
    onProgressChange?.(updated);

    try {
      if (roadmapData?.id) {
        await api.updateRoadmapProgress(roadmapData.id, taskId, isDone);
      }
    } catch (err) {
      console.error("Failed to persist progress:", err);
    }
  };

  const handleExportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(roadmapData, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `fitness_roadmap_${roadmap.goal || "plan"}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div style={{ maxWidth: 1040, margin: "0 auto", padding: "20px 24px 60px" }}>
      {/* ── Top Header Banner ─────────────────────────────────────────────── */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(28,27,27,0.95), rgba(32,31,31,0.85))",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 16,
          padding: "24px 28px",
          marginBottom: 24,
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: -40,
            right: -40,
            width: 180,
            height: 180,
            background: "radial-gradient(circle, rgba(0,212,170,0.12) 0%, transparent 70%)",
            borderRadius: "50%",
            pointerEvents: "none",
          }}
        />

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <span
                style={{
                  fontFamily: T.fontD,
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: "0.16em",
                  textTransform: "uppercase",
                  padding: "4px 10px",
                  borderRadius: 6,
                  background: "rgba(0, 212, 170, 0.12)",
                  color: T.primary,
                }}
              >
                {roadmap.goal ? roadmap.goal.replace("_", " ") : "FITNESS"} · {roadmap.level || "INTERMEDIATE"}
              </span>
              <span
                style={{
                  fontFamily: T.fontD,
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  padding: "4px 10px",
                  borderRadius: 6,
                  background: "rgba(255,255,255,0.06)",
                  color: T.dim,
                }}
              >
                ENGINE: {roadmapData?.provider_used || "AI LLM"}
              </span>
            </div>

            <h1
              style={{
                fontFamily: T.fontD,
                fontSize: "clamp(22px, 3.5vw, 32px)",
                fontWeight: 700,
                letterSpacing: "-0.02em",
                color: T.text,
                margin: "0 0 10px",
              }}
            >
              {roadmap.title || "Personalized Fitness & Nutrition Master Roadmap"}
            </h1>

            <p style={{ fontFamily: T.fontB, fontSize: 13, color: T.silver, maxWidth: 740, lineHeight: 1.6, margin: 0 }}>
              {roadmap.overview_summary}
            </p>
          </div>

          {/* Action Tools */}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <button
              onClick={() => setShowHistoryModal(true)}
              style={{
                fontFamily: T.fontD,
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                padding: "8px 14px",
                borderRadius: 8,
                border: "1px solid rgba(255,255,255,0.08)",
                background: T.surface,
                color: T.silver,
                cursor: "pointer",
              }}
            >
              📁 HISTORY
            </button>
            <button
              onClick={handleExportJSON}
              style={{
                fontFamily: T.fontD,
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                padding: "8px 14px",
                borderRadius: 8,
                border: "1px solid rgba(255,255,255,0.08)",
                background: T.surface,
                color: T.silver,
                cursor: "pointer",
              }}
            >
              💾 EXPORT
            </button>
            <button
              onClick={onRegenerate}
              style={{
                fontFamily: T.fontD,
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                padding: "8px 16px",
                borderRadius: 8,
                border: "none",
                background: `linear-gradient(135deg, ${T.primary}, ${T.primaryD})`,
                color: "#131313",
                cursor: "pointer",
              }}
            >
              + NEW ROADMAP
            </button>
          </div>
        </div>

        {/* ── Macro Dashboard Badges ──────────────────────────────────────── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: 10,
            marginTop: 20,
            paddingTop: 18,
            borderTop: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          <div style={{ background: T.surface, padding: "12px 14px", borderRadius: 10 }}>
            <div style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: T.dim, textTransform: "uppercase" }}>
              DAILY CALORIES
            </div>
            <div style={{ fontFamily: T.fontD, fontSize: 18, fontWeight: 700, color: T.text, marginTop: 4 }}>
              {targetMacros.calories} <span style={{ fontSize: 11, color: T.dim }}>kcal</span>
            </div>
          </div>

          <div style={{ background: T.surface, padding: "12px 14px", borderRadius: 10 }}>
            <div style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: T.primary, textTransform: "uppercase" }}>
              PROTEIN TARGET
            </div>
            <div style={{ fontFamily: T.fontD, fontSize: 18, fontWeight: 700, color: T.primary, marginTop: 4 }}>
              {targetMacros.protein_g}g <span style={{ fontSize: 11, color: T.dim }}>/ day</span>
            </div>
          </div>

          <div style={{ background: T.surface, padding: "12px 14px", borderRadius: 10 }}>
            <div style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: T.info, textTransform: "uppercase" }}>
              CARBOHYDRATES
            </div>
            <div style={{ fontFamily: T.fontD, fontSize: 18, fontWeight: 700, color: T.info, marginTop: 4 }}>
              {targetMacros.carbs_g}g <span style={{ fontSize: 11, color: T.dim }}>/ day</span>
            </div>
          </div>

          <div style={{ background: T.surface, padding: "12px 14px", borderRadius: 10 }}>
            <div style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: T.warning, textTransform: "uppercase" }}>
              HEALTHY FATS
            </div>
            <div style={{ fontFamily: T.fontD, fontSize: 18, fontWeight: 700, color: T.warning, marginTop: 4 }}>
              {targetMacros.fat_g}g <span style={{ fontSize: 11, color: T.dim }}>/ day</span>
            </div>
          </div>

          <div style={{ background: T.surface, padding: "12px 14px", borderRadius: 10 }}>
            <div style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: T.success, textTransform: "uppercase" }}>
              HYDRATION
            </div>
            <div style={{ fontFamily: T.fontD, fontSize: 18, fontWeight: 700, color: T.success, marginTop: 4 }}>
              {targetMacros.hydration_liters}L <span style={{ fontSize: 11, color: T.dim }}>water</span>
            </div>
          </div>

          <div style={{ background: T.surface, padding: "12px 14px", borderRadius: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: T.dim, textTransform: "uppercase" }}>
                PROGRESS
              </span>
              <span style={{ fontFamily: T.fontD, fontSize: 11, fontWeight: 700, color: T.primary }}>
                {completionPercentage}%
              </span>
            </div>
            <div style={{ width: "100%", height: 6, background: "#2a2a2a", borderRadius: 3, marginTop: 8, overflow: "hidden" }}>
              <div
                style={{
                  width: `${completionPercentage}%`,
                  height: "100%",
                  background: `linear-gradient(90deg, ${T.primary}, ${T.primaryD})`,
                  borderRadius: 3,
                  transition: "width 0.4s ease",
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* ── Week Switcher Tabs ────────────────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontFamily: T.fontD, fontSize: 10, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: T.dim, marginBottom: 8 }}>
          PERIODIZATION TIMELINE ({weeks.length} WEEKS)
        </div>
        <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 4 }}>
          {weeks.map((w, idx) => {
            const active = selectedWeekIdx === idx;
            return (
              <button
                key={w.week_number || idx}
                onClick={() => setSelectedWeekIdx(idx)}
                style={{
                  flex: "1 0 160px",
                  padding: "12px 16px",
                  borderRadius: 12,
                  cursor: "pointer",
                  border: active ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.06)",
                  background: active ? "rgba(0, 212, 170, 0.08)" : T.surface,
                  textAlign: "left",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontFamily: T.fontD, fontSize: 11, fontWeight: 700, color: active ? T.primary : T.silver }}>
                    WEEK {w.week_number}
                  </span>
                  {active && <span style={{ width: 6, height: 6, borderRadius: "50%", background: T.primary }} />}
                </div>
                <div style={{ fontFamily: T.fontB, fontSize: 11, color: active ? T.text : T.dim, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {w.phase_name ? w.phase_name.split(":")[0] : `Phase ${idx + 1}`}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Phase Focus Callout ────────────────────────────────────────────── */}
      {currentWeek && (
        <div
          style={{
            background: T.surface,
            borderRadius: 12,
            padding: "14px 20px",
            marginBottom: 24,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 10,
            borderLeft: `3px solid ${T.primary}`,
          }}
        >
          <div>
            <span style={{ fontFamily: T.fontD, fontSize: 10, fontWeight: 700, color: T.primary, letterSpacing: "0.1em", textTransform: "uppercase" }}>
              WEEK {currentWeek.week_number}: {currentWeek.phase_name}
            </span>
            <div style={{ fontFamily: T.fontB, fontSize: 12, color: T.silver, marginTop: 2 }}>
              {currentWeek.phase_focus}
            </div>
          </div>
        </div>
      )}

      {/* ── Feature Sub-Navigation ─────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20, borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: 10 }}>
        {[
          { id: "workouts", label: "🏋️ WORKOUT SPLIT", count: currentWeek.workout_days?.length },
          { id: "nutrition", label: "🥗 NUTRITION & MEALS", count: currentWeek.nutrition_plan?.meal_slots?.length },
          { id: "milestones", label: "🎯 MILESTONES & TARGETS", count: currentWeek.milestones?.length },
          { id: "recovery", label: "🧘 RECOVERY & COACHING" },
        ].map((tab) => {
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                fontFamily: T.fontD,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: "0.08em",
                padding: "8px 16px",
                borderRadius: 8,
                border: "none",
                cursor: "pointer",
                background: active ? `linear-gradient(135deg, ${T.primary}, ${T.primaryD})` : "transparent",
                color: active ? "#131313" : T.dim,
                transition: "all 0.15s ease",
              }}
            >
              {tab.label} {tab.count !== undefined && `(${tab.count})`}
            </button>
          );
        })}
      </div>

      {/* ── SUB-TAB 1: WORKOUT SPLIT ───────────────────────────────────────── */}
      {activeTab === "workouts" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {(currentWeek.workout_days || []).map((day, dIdx) => {
            const isRest = day.is_rest_day;
            return (
              <div
                key={day.day_number || dIdx}
                style={{
                  background: T.surface,
                  borderRadius: 14,
                  border: isRest ? "1px solid rgba(255,255,255,0.04)" : "1px solid rgba(255,255,255,0.08)",
                  padding: "20px 22px",
                  animation: "fadeUp 0.25s ease",
                }}
              >
                {/* Day Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span
                        style={{
                          fontFamily: T.fontD,
                          fontSize: 13,
                          fontWeight: 700,
                          color: isRest ? T.dim : T.text,
                        }}
                      >
                        {day.day_name}
                      </span>
                      {isRest && (
                        <span
                          style={{
                            fontFamily: T.fontD,
                            fontSize: 9,
                            fontWeight: 700,
                            padding: "3px 8px",
                            borderRadius: 4,
                            background: "rgba(151,196,89,0.12)",
                            color: T.success,
                            textTransform: "uppercase",
                          }}
                        >
                          REST / ACTIVE RECOVERY
                        </span>
                      )}
                    </div>
                    <div style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim, marginTop: 2 }}>
                      Focus: {day.focus_area} · {day.duration_minutes} Minutes
                    </div>
                  </div>
                </div>

                {/* Warmup */}
                {day.warmup?.length > 0 && (
                  <div style={{ background: T.bg, borderRadius: 8, padding: "10px 14px", marginBottom: 14 }}>
                    <div style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, color: T.dim, textTransform: "uppercase", marginBottom: 4 }}>
                      🔥 DYNAMIC WARM-UP
                    </div>
                    <div style={{ fontFamily: T.fontB, fontSize: 12, color: T.silver, lineHeight: 1.5 }}>
                      {day.warmup.join("  ·  ")}
                    </div>
                  </div>
                )}

                {/* Exercises Table */}
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {(day.exercises || []).map((ex, eIdx) => {
                    const checked = !!localProgress[ex.id];
                    return (
                      <div
                        key={ex.id || eIdx}
                        style={{
                          background: checked ? "rgba(0, 212, 170, 0.04)" : T.card,
                          border: checked ? "1px solid rgba(0, 212, 170, 0.25)" : "1px solid rgba(255,255,255,0.04)",
                          borderRadius: 10,
                          padding: "12px 16px",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          flexWrap: "wrap",
                          gap: 12,
                          transition: "all 0.15s ease",
                        }}
                      >
                        {/* Checkbox & Exercise info */}
                        <div style={{ display: "flex", alignItems: "flex-start", gap: 12, flex: 1, minWidth: 260 }}>
                          <button
                            type="button"
                            onClick={() => handleToggleTask(ex.id)}
                            style={{
                              width: 22,
                              height: 22,
                              borderRadius: 6,
                              border: checked ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.2)",
                              background: checked ? T.primary : "transparent",
                              color: "#131313",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontSize: 13,
                              fontWeight: 700,
                              cursor: "pointer",
                              flexShrink: 0,
                              marginTop: 2,
                            }}
                          >
                            {checked ? "✓" : ""}
                          </button>

                          <div>
                            <div
                              style={{
                                fontFamily: T.fontD,
                                fontSize: 13,
                                fontWeight: 700,
                                color: checked ? T.dim : T.text,
                                textDecoration: checked ? "line-through" : "none",
                              }}
                            >
                              {ex.name}
                            </div>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                              {(ex.target_muscles || []).map((m, i) => (
                                <span
                                  key={i}
                                  style={{
                                    fontFamily: T.fontB,
                                    fontSize: 10,
                                    color: T.dim,
                                    background: "rgba(255,255,255,0.04)",
                                    padding: "2px 6px",
                                    borderRadius: 4,
                                  }}
                                >
                                  {m}
                                </span>
                              ))}
                            </div>
                            {ex.form_cues?.length > 0 && (
                              <div style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim, marginTop: 4, fontStyle: "italic" }}>
                                Cue: {ex.form_cues.join(" | ")}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Sets & Intensity Metrics */}
                        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                          <div style={{ textAlign: "center" }}>
                            <div style={{ fontFamily: T.fontD, fontSize: 8, fontWeight: 700, color: T.dim, textTransform: "uppercase" }}>
                              SETS × REPS
                            </div>
                            <div style={{ fontFamily: T.fontD, fontSize: 12, fontWeight: 700, color: T.text }}>
                              {ex.sets} × {ex.reps}
                            </div>
                          </div>

                          <div style={{ textAlign: "center" }}>
                            <div style={{ fontFamily: T.fontD, fontSize: 8, fontWeight: 700, color: T.dim, textTransform: "uppercase" }}>
                              INTENSITY
                            </div>
                            <div style={{ fontFamily: T.fontD, fontSize: 11, fontWeight: 600, color: T.info }}>
                              {ex.intensity}
                            </div>
                          </div>

                          <div style={{ textAlign: "center" }}>
                            <div style={{ fontFamily: T.fontD, fontSize: 8, fontWeight: 700, color: T.dim, textTransform: "uppercase" }}>
                              REST
                            </div>
                            <div style={{ fontFamily: T.fontD, fontSize: 11, color: T.dim }}>
                              {ex.rest_seconds > 0 ? `${ex.rest_seconds}s` : "—"}
                            </div>
                          </div>

                          {/* Quick Deep-link to Form AI */}
                          <button
                            type="button"
                            onClick={() => navigate("/pose")}
                            title="Test biomechanics in Form AI"
                            style={{
                              fontFamily: T.fontD,
                              fontSize: 9,
                              fontWeight: 700,
                              letterSpacing: "0.06em",
                              textTransform: "uppercase",
                              padding: "6px 10px",
                              borderRadius: 6,
                              border: "1px solid rgba(0, 212, 170, 0.3)",
                              background: "rgba(0, 212, 170, 0.08)",
                              color: T.primary,
                              cursor: "pointer",
                              whiteSpace: "nowrap",
                            }}
                          >
                            📷 FORM AI
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Cooldown */}
                {day.cooldown?.length > 0 && (
                  <div style={{ marginTop: 12, padding: "8px 12px", background: "rgba(255,255,255,0.02)", borderRadius: 8 }}>
                    <span style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, color: T.dim, textTransform: "uppercase" }}>
                      ❄️ COOLDOWN:
                    </span>{" "}
                    <span style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim }}>
                      {day.cooldown.join(" · ")}
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── SUB-TAB 2: NUTRITION & MEAL PLAN ───────────────────────────────── */}
      {activeTab === "nutrition" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Nutrition Meta Callout */}
          <div style={{ background: T.surface, borderRadius: 14, padding: "18px 22px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
              <div>
                <div style={{ fontFamily: T.fontD, fontSize: 10, fontWeight: 700, color: T.primary, textTransform: "uppercase", letterSpacing: "0.12em" }}>
                  WEEKLY DIETARY ARCHITECTURE
                </div>
                <div style={{ fontFamily: T.fontB, fontSize: 13, color: T.silver, marginTop: 4 }}>
                  {currentWeek.nutrition_plan?.dietary_notes || "Precision macronutrient distribution tailored to fuel workouts and optimize recovery."}
                </div>
              </div>
              <button
                onClick={() => navigate("/nutrition")}
                style={{
                  padding: "8px 16px",
                  borderRadius: 8,
                  border: "1px solid rgba(0, 212, 170, 0.3)",
                  background: "rgba(0, 212, 170, 0.1)",
                  color: T.primary,
                  fontFamily: T.fontD,
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  cursor: "pointer",
                }}
              >
                📊 OPEN NUTRITION TRACKER →
              </button>
            </div>
          </div>

          {/* Meal Slots */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 12 }}>
            {(currentWeek.nutrition_plan?.meal_slots || []).map((slot, sIdx) => {
              const opt = slot.options?.[0] || {};
              return (
                <div
                  key={slot.slot_id || sIdx}
                  style={{
                    background: T.surface,
                    borderRadius: 14,
                    padding: "18px 20px",
                    border: "1px solid rgba(255,255,255,0.06)",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <span style={{ fontFamily: T.fontD, fontSize: 11, fontWeight: 700, color: T.primary, textTransform: "uppercase" }}>
                        {slot.slot_title}
                      </span>
                      <span style={{ fontFamily: T.fontB, fontSize: 10, color: T.dim }}>{slot.time_window}</span>
                    </div>

                    <h4 style={{ fontFamily: T.fontD, fontSize: 14, fontWeight: 700, color: T.text, margin: "0 0 10px" }}>
                      {opt.name || "Balanced Nutrition Plate"}
                    </h4>

                    {/* Macros pills */}
                    <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                      <span style={{ background: "rgba(255,255,255,0.05)", padding: "3px 8px", borderRadius: 6, fontFamily: T.fontD, fontSize: 10, color: T.silver }}>
                        🔥 {opt.calories} kcal
                      </span>
                      <span style={{ background: "rgba(0, 212, 170, 0.08)", padding: "3px 8px", borderRadius: 6, fontFamily: T.fontD, fontSize: 10, color: T.primary }}>
                        🥩 {opt.protein_g}g P
                      </span>
                      <span style={{ background: "rgba(133, 183, 235, 0.08)", padding: "3px 8px", borderRadius: 6, fontFamily: T.fontD, fontSize: 10, color: T.info }}>
                        🌾 {opt.carbs_g}g C
                      </span>
                      <span style={{ background: "rgba(245, 166, 35, 0.08)", padding: "3px 8px", borderRadius: 6, fontFamily: T.fontD, fontSize: 10, color: T.warning }}>
                        🥑 {opt.fat_g}g F
                      </span>
                    </div>

                    {/* Ingredients */}
                    {opt.ingredients?.length > 0 && (
                      <div style={{ marginBottom: 10 }}>
                        <div style={{ fontFamily: T.fontD, fontSize: 8, fontWeight: 700, color: T.dim, textTransform: "uppercase", marginBottom: 4 }}>
                          INGREDIENTS
                        </div>
                        <div style={{ fontFamily: T.fontB, fontSize: 11, color: T.silver, lineHeight: 1.4 }}>
                          {opt.ingredients.join(", ")}
                        </div>
                      </div>
                    )}

                    {/* Recipe tips */}
                    {opt.recipe_tips && (
                      <div style={{ fontFamily: T.fontB, fontSize: 10, color: T.dim, fontStyle: "italic", borderTop: "1px solid rgba(255,255,255,0.04)", paddingTop: 8 }}>
                        💡 {opt.recipe_tips}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Supplement Protocol */}
          {currentWeek.nutrition_plan?.supplement_protocol?.length > 0 && (
            <div style={{ background: T.surface, borderRadius: 14, padding: "18px 22px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontFamily: T.fontD, fontSize: 10, fontWeight: 700, color: T.warning, textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 10 }}>
                💊 TARGETED SUPPLEMENT PROTOCOL
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10 }}>
                {currentWeek.nutrition_plan.supplement_protocol.map((supp, i) => (
                  <div key={i} style={{ background: T.bg, padding: "10px 14px", borderRadius: 8, fontFamily: T.fontB, fontSize: 12, color: T.silver }}>
                    • {supp}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── SUB-TAB 3: MILESTONES ───────────────────────────────────────────── */}
      {activeTab === "milestones" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {(currentWeek.milestones || []).map((m, mIdx) => {
            const checked = !!localProgress[m.id];
            return (
              <div
                key={m.id || mIdx}
                style={{
                  background: checked ? "rgba(0, 212, 170, 0.05)" : T.surface,
                  border: checked ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.06)",
                  borderRadius: 14,
                  padding: "18px 22px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 16,
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
                  <button
                    type="button"
                    onClick={() => handleToggleTask(m.id)}
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: 6,
                      border: checked ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.2)",
                      background: checked ? T.primary : "transparent",
                      color: "#131313",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 14,
                      fontWeight: 700,
                      cursor: "pointer",
                      flexShrink: 0,
                      marginTop: 2,
                    }}
                  >
                    {checked ? "✓" : ""}
                  </button>
                  <div>
                    <h4
                      style={{
                        fontFamily: T.fontD,
                        fontSize: 14,
                        fontWeight: 700,
                        color: checked ? T.dim : T.text,
                        margin: "0 0 4px",
                        textDecoration: checked ? "line-through" : "none",
                      }}
                    >
                      {m.title}
                    </h4>
                    <div style={{ fontFamily: T.fontB, fontSize: 12, color: T.silver, lineHeight: 1.5 }}>
                      {m.description}
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    background: "rgba(0, 212, 170, 0.08)",
                    border: "1px solid rgba(0, 212, 170, 0.2)",
                    borderRadius: 8,
                    padding: "8px 14px",
                    textAlign: "right",
                    flexShrink: 0,
                  }}
                >
                  <div style={{ fontFamily: T.fontD, fontSize: 8, fontWeight: 700, color: T.primary, textTransform: "uppercase" }}>
                    BENCHMARK GOAL
                  </div>
                  <div style={{ fontFamily: T.fontD, fontSize: 11, fontWeight: 700, color: T.text, marginTop: 2 }}>
                    {m.metric_goal}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── SUB-TAB 4: RECOVERY & COACHING ─────────────────────────────────── */}
      {activeTab === "recovery" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ background: T.surface, borderRadius: 14, padding: "20px 24px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontFamily: T.fontD, fontSize: 10, fontWeight: 700, color: T.success, textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 12 }}>
              😴 RECOVERY & NEURAL ADAPTATION PROTOCOL
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {(currentWeek.recovery_protocol || []).map((rec, i) => (
                <div
                  key={i}
                  style={{
                    background: T.bg,
                    padding: "12px 16px",
                    borderRadius: 8,
                    fontFamily: T.fontB,
                    fontSize: 12,
                    color: T.silver,
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                  }}
                >
                  <span style={{ color: T.success }}>✔</span>
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: T.surface, borderRadius: 14, padding: "20px 24px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontFamily: T.fontD, fontSize: 10, fontWeight: 700, color: T.primary, textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 12 }}>
              🧠 GENERAL HABITS & ADHERENCE
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 10 }}>
              {(roadmap.key_habits || []).map((habit, i) => (
                <div key={i} style={{ background: T.bg, padding: "12px 14px", borderRadius: 8, fontFamily: T.fontB, fontSize: 11, color: T.silver }}>
                  ⚡ {habit}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── History Drawer / Modal ────────────────────────────────────────── */}
      {showHistoryModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.75)",
            backdropFilter: "blur(8px)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div
            style={{
              background: T.surface,
              borderRadius: 16,
              border: "1px solid rgba(255,255,255,0.08)",
              padding: "24px 28px",
              width: "100%",
              maxWidth: 620,
              maxHeight: "80vh",
              overflowY: "auto",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <h3 style={{ fontFamily: T.fontD, fontSize: 16, fontWeight: 700, color: T.text, margin: 0 }}>
                SAVED ROADMAPS HISTORY
              </h3>
              <button
                onClick={() => setShowHistoryModal(false)}
                style={{ background: "none", border: "none", color: T.dim, fontSize: 18, cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {history.length === 0 ? (
                <div style={{ textAlign: "center", color: T.dim, padding: "20px 0", fontFamily: T.fontB }}>
                  No previous roadmaps found.
                </div>
              ) : (
                history.map((h) => (
                  <div
                    key={h.id}
                    style={{
                      background: h.active ? "rgba(0, 212, 170, 0.08)" : T.bg,
                      border: h.active ? `1px solid ${T.primary}` : "1px solid rgba(255,255,255,0.05)",
                      borderRadius: 10,
                      padding: "14px 16px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <div style={{ fontFamily: T.fontD, fontSize: 12, fontWeight: 700, color: T.text }}>
                        {h.title || `${h.duration_weeks}-Week ${h.goal} Plan`}
                      </div>
                      <div style={{ fontFamily: T.fontB, fontSize: 10, color: T.dim, marginTop: 4 }}>
                        {h.duration_weeks} Weeks · {h.level} · {new Date(h.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {h.active ? (
                        <span style={{ fontFamily: T.fontD, fontSize: 10, fontWeight: 700, color: T.primary }}>ACTIVE</span>
                      ) : (
                        <button
                          onClick={async () => {
                            await onSwitchRoadmap?.(h.id);
                            setShowHistoryModal(false);
                          }}
                          style={{
                            padding: "6px 12px",
                            borderRadius: 6,
                            border: "1px solid rgba(255,255,255,0.1)",
                            background: T.surface,
                            color: T.silver,
                            fontFamily: T.fontD,
                            fontSize: 10,
                            fontWeight: 700,
                            cursor: "pointer",
                          }}
                        >
                          ACTIVATE
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
