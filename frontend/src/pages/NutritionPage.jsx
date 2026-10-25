/**
 * NutritionPage.jsx — The All Fit Design System
 * Dark editorial aesthetic with Space Grotesk + Lexend typography
 */
import React, { useState, useRef, useCallback, useEffect } from "react";
import api from "../services/api";

// ── Fonts ─────────────────────────────────────────────────────────────────────
const FONT_IMPORT = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Lexend:wght@300;400;500;600&display=swap');
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(0,212,170,0.3); }
    50% { box-shadow: 0 0 0 12px rgba(0,212,170,0); }
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes shimmer {
    0%   { background-position: -400px 0; }
    100% { background-position: 400px 0; }
  }
`;

// ── Design tokens ─────────────────────────────────────────────────────────────
const T = {
  bg:       "#131313",
  surface:  "#1c1b1b",
  card:     "#201f1f",
  cardHigh: "#2a2a2a",
  primary:  "#00d4aa",
  primaryD: "#00b896",
  silver:   "#c8c6c6",
  dim:      "#888580",
  error:    "#ffb4ab",
  fontD:    "'Space Grotesk', sans-serif",
  fontB:    "'Lexend', sans-serif",
};

// ── Macro goals ───────────────────────────────────────────────────────────────
const GOALS = { calories: 2450, protein: 185, carbs: 210, fat: 72, fiber: 35 };

const QUICK = [
  "chicken breast", "oats", "banana", "dal chapati", "paneer",
  "brown rice", "eggs", "salmon", "sweet potato", "biryani",
  "greek yogurt", "almonds", "masala dosa", "protein shake", "avocado",
];

// ── Helpers ───────────────────────────────────────────────────────────────────
const todayKey = () => `kl_nutrition_${new Date().toISOString().slice(0, 10)}`;
const loadToday = () => { try { return JSON.parse(localStorage.getItem(todayKey()) || "[]"); } catch { return []; } };
const saveToday = (items) => localStorage.setItem(todayKey(), JSON.stringify(items));
const r = (v, d = 1) => Math.round((v || 0) * Math.pow(10, d)) / Math.pow(10, d);

// ── MacroArc ──────────────────────────────────────────────────────────────────
function MacroArc({ value, goal, color, label, unit = "g" }) {
  const pct = Math.min(1, value / goal);
  const R = 28, C = 2 * Math.PI * R;
  const over = value > goal;
  return (
    <div style={{ textAlign: "center", fontFamily: T.fontD }}>
      <div style={{ position: "relative", width: 72, height: 72, margin: "0 auto 6px" }}>
        <svg width="72" height="72" style={{ transform: "rotate(-90deg)" }}>
          <circle cx="36" cy="36" r={R} fill="none" stroke={T.cardHigh} strokeWidth="5" />
          <circle cx="36" cy="36" r={R} fill="none"
            stroke={over ? T.error : color} strokeWidth="5"
            strokeDasharray={C} strokeDashoffset={C * (1 - pct)}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(.4,0,.2,1)" }} />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center",
          justifyContent: "center", flexDirection: "column" }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: over ? T.error : color, lineHeight: 1 }}>
            {Math.round(value)}
          </span>
          <span style={{ fontSize: 8, color: T.dim, letterSpacing: "0.05em" }}>{unit}</span>
        </div>
      </div>
      <div style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase",
        letterSpacing: "0.08em", color: T.dim }}>{label}</div>
      <div style={{ fontSize: 8, color: T.cardHigh === "#2a2a2a" ? "#444" : T.dim, marginTop: 1 }}>
        / {goal}
      </div>
    </div>
  );
}

// ── MacroBar ──────────────────────────────────────────────────────────────────
function MacroBar({ label, value, goal, color }) {
  const pct = Math.min(100, (value / goal) * 100);
  const over = value > goal;
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between",
        fontFamily: T.fontB, fontSize: 12, marginBottom: 5 }}>
        <span style={{ color: T.silver, fontWeight: 500 }}>{label}</span>
        <span style={{ color: over ? T.error : T.silver }}>
          <strong style={{ color: over ? T.error : color }}>{r(value)}</strong>
          <span style={{ color: T.dim }}> / {goal}g</span>
        </span>
      </div>
      <div style={{ height: 4, background: T.cardHigh, borderRadius: 2, overflow: "hidden" }}>
        <div style={{
          width: `${pct}%`, height: "100%", borderRadius: 2,
          background: over ? T.error : `linear-gradient(90deg, ${color}, ${color}cc)`,
          transition: "width 0.8s cubic-bezier(.4,0,.2,1)",
        }} />
      </div>
    </div>
  );
}

// ── FoodCard ──────────────────────────────────────────────────────────────────
function FoodCard({ food, onAdd, index }) {
  const [qty, setQty] = useState(100);
  const [adding, setAdding] = useState(false);
  const scale = qty / 100;
  const sc = (v) => r((v || 0) * scale);

  const handleAdd = async () => {
    setAdding(true);
    onAdd({ name: food.name, qty, calories: sc(food.calories), protein: sc(food.protein),
      carbs: sc(food.carbs), fat: sc(food.fat), fiber: sc(food.fiber) });
    setTimeout(() => setAdding(false), 600);
  };

  return (
    <div style={{
      background: T.card, borderRadius: 12, padding: "16px 18px", marginBottom: 8,
      animation: `fadeUp 0.3s ease both`, animationDelay: `${index * 0.06}s`,
      border: `1px solid rgba(81,69,54,0.15)`,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
        <div>
          <div style={{ fontFamily: T.fontD, fontWeight: 600, fontSize: 14, color: "#e8e6df" }}>
            {food.name}
          </div>
          <div style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim, marginTop: 2 }}>
            {food.serving_note || "per 100g"}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <span style={{ fontFamily: T.fontD, fontSize: 22, fontWeight: 700,
            background: `linear-gradient(135deg, ${T.primary}, ${T.primaryD})`,
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            {sc(food.calories)}
          </span>
          <span style={{ fontFamily: T.fontB, fontSize: 10, color: T.dim, marginLeft: 3 }}>kcal</span>
        </div>
      </div>

      <div style={{ display: "flex", gap: 6, marginBottom: 14 }}>
        {[
          { l: "PROT", v: sc(food.protein), c: "#4ade80" },
          { l: "CARB", v: sc(food.carbs),   c: T.primary },
          { l: "FAT",  v: sc(food.fat),      c: "#f87171" },
          ...(food.fiber > 0.5 ? [{ l: "FIBER", v: sc(food.fiber), c: "#38bdf8" }] : []),
        ].map(({ l, v, c }) => (
          <div key={l} style={{ flex: 1, background: T.cardHigh, borderRadius: 8,
            padding: "8px 4px", textAlign: "center" }}>
            <div style={{ fontFamily: T.fontD, fontSize: 14, fontWeight: 700, color: c }}>{v}</div>
            <div style={{ fontFamily: T.fontB, fontSize: 8, color: T.dim, letterSpacing: "0.07em",
              textTransform: "uppercase", marginTop: 2 }}>{l}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6,
          background: T.cardHigh, borderRadius: 8, padding: "6px 10px", flex: "0 0 auto" }}>
          <span style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim }}>g</span>
          <input type="number" value={qty} min={1} max={3000}
            onChange={e => setQty(Math.max(1, parseInt(e.target.value) || 100))}
            style={{ width: 52, background: "transparent", border: "none", outline: "none",
              fontFamily: T.fontD, fontSize: 14, fontWeight: 600, color: "#e8e6df",
              textAlign: "center" }} />
        </div>
        <button onClick={handleAdd}
          style={{ flex: 1, padding: "9px 0", borderRadius: 8, border: "none",
            background: adding
              ? `linear-gradient(135deg, #4ade80, #22c55e)`
              : `linear-gradient(135deg, ${T.primary}, ${T.primaryD})`,
            color: "#131313", fontFamily: T.fontD, fontSize: 13, fontWeight: 700,
            cursor: "pointer", transition: "all 0.3s ease",
            letterSpacing: "0.03em" }}>
          {adding ? "✓ ADDED" : "+ LOG FOOD"}
        </button>
      </div>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function NutritionPage() {
  const [query,   setQuery]   = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");
  const [logged,  setLogged]  = useState(loadToday);
  const [source,  setSource]  = useState("");
  const timerRef = useRef(null);

  const totals = logged.reduce((acc, i) => ({
    calories: acc.calories + (i.calories || 0),
    protein:  acc.protein  + (i.protein  || 0),
    carbs:    acc.carbs    + (i.carbs    || 0),
    fat:      acc.fat      + (i.fat      || 0),
    fiber:    acc.fiber    + (i.fiber    || 0),
  }), { calories: 0, protein: 0, carbs: 0, fat: 0, fiber: 0 });

  const calRemaining = Math.max(0, GOALS.calories - Math.round(totals.calories));
  const compliance   = Math.round(Math.min(100, (Math.round(totals.calories) / GOALS.calories) * 100));

  const doSearch = useCallback(async (q) => {
    if (!q.trim() || q.trim().length < 2) { setResults([]); return; }
    setLoading(true); setError(""); setSource("");
    try {
      const data = await api._fetch("/api/v1/nutrition/search", {
        method: "POST", body: JSON.stringify({ query: q }),
      });
      setResults(data.foods || []);
      setSource(data.source || "");
    } catch (e) {
      setError(e.message || "Search failed");
      setResults([]);
    }
    setLoading(false);
  }, []);

  const handleInput = (e) => {
    const val = e.target.value;
    setQuery(val);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => doSearch(val), 600);
  };

  const addFood = (item) => {
    const next = [{ ...item, id: Date.now() }, ...logged];
    setLogged(next); saveToday(next);
    setResults([]); setQuery("");
  };

  const removeFood = (id) => {
    const next = logged.filter(i => i.id !== id);
    setLogged(next); saveToday(next);
  };

  const sourceBadge = { usda: "USDA", nutritionix: "NUTRITIONIX",
    open_food_facts: "OFF", gemini: "AI", groq: "AI", ollama: "LOCAL AI" };

  return (
    <>
      <style>{FONT_IMPORT}</style>
      <div style={{ minHeight: "100vh", background: T.bg, fontFamily: T.fontB, padding: "0 0 60px" }}>

        {/* ── Hero Header ── */}
        <div style={{ padding: "36px 28px 28px", borderBottom: `1px solid rgba(255,255,255,0.04)` }}>
          <div style={{ maxWidth: 900, margin: "0 auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 20 }}>
              <div>
                <p style={{ fontFamily: T.fontD, fontSize: 10, fontWeight: 600, letterSpacing: "0.18em",
                  textTransform: "uppercase", color: T.primary, marginBottom: 10 }}>
                  FUEL OPTIMIZATION
                </p>
                <h1 style={{ fontFamily: T.fontD, fontSize: "clamp(36px,5vw,60px)", fontWeight: 700,
                  lineHeight: 0.95, letterSpacing: "-0.02em", color: "#e8e6df", margin: 0 }}>
                  NUTRITION<br />
                  <span style={{ color: T.cardHigh, WebkitTextStroke: `1px ${T.dim}` }}>INTELLIGENCE</span>
                </h1>
              </div>

              {/* Daily status widget */}
              <div style={{ background: T.surface, borderRadius: 14, padding: "18px 22px",
                minWidth: 220, border: `1px solid rgba(0,212,170,0.12)` }}>
                <div style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 600,
                  letterSpacing: "0.14em", textTransform: "uppercase", color: T.dim, marginBottom: 6 }}>
                  DAILY STATUS
                </div>
                <div style={{ fontFamily: T.fontD, fontSize: 28, fontWeight: 700,
                  background: `linear-gradient(135deg, ${T.primary}, ${T.primaryD})`,
                  WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: 12 }}>
                  {compliance}% COMPLIANCE
                </div>
                <button
                  onClick={() => document.getElementById("kl-search")?.focus()}
                  style={{ width: "100%", padding: "9px 0", borderRadius: 8, border: `1px solid ${T.primary}`,
                    background: "transparent", color: T.primary, fontFamily: T.fontD, fontSize: 12,
                    fontWeight: 700, cursor: "pointer", letterSpacing: "0.08em" }}>
                  + LOG FOOD
                </button>
              </div>
            </div>
          </div>
        </div>

        <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 28px" }}>

          {/* ── Macro Balance ── */}
          <div style={{ marginTop: 28, display: "grid", gridTemplateColumns: "1fr auto", gap: 16 }}>
            <div style={{ background: T.surface, borderRadius: 16, padding: "22px 24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
                <div>
                  <h2 style={{ fontFamily: T.fontD, fontSize: 14, fontWeight: 700, letterSpacing: "0.05em",
                    textTransform: "uppercase", color: "#e8e6df", margin: "0 0 4px" }}>
                    DAILY MACRO BALANCE
                  </h2>
                  <p style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim, margin: 0 }}>
                    Real-time macronutrient distribution
                  </p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontFamily: T.fontD, fontSize: 32, fontWeight: 700,
                    background: `linear-gradient(135deg, ${T.primary}, ${T.primaryD})`,
                    WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", lineHeight: 1 }}>
                    {calRemaining.toLocaleString()}
                  </div>
                  <div style={{ fontFamily: T.fontB, fontSize: 9, letterSpacing: "0.1em",
                    textTransform: "uppercase", color: T.dim, marginTop: 3 }}>
                    KCAL REMAINING
                  </div>
                </div>
              </div>

              <MacroBar label="Protein"  value={r(totals.protein)}  goal={GOALS.protein}  color="#4ade80" />
              <MacroBar label="Carbs"    value={r(totals.carbs)}    goal={GOALS.carbs}    color={T.primary} />
              <MacroBar label="Fat"      value={r(totals.fat)}      goal={GOALS.fat}      color="#f87171" />
              <MacroBar label="Fiber"    value={r(totals.fiber)}    goal={GOALS.fiber}    color="#38bdf8" />
            </div>

            {/* Arc charts */}
            <div style={{ background: T.surface, borderRadius: 16, padding: "22px 18px",
              display: "flex", flexDirection: "column", gap: 16, justifyContent: "center", minWidth: 96 }}>
              <MacroArc value={r(totals.protein)} goal={GOALS.protein} color="#4ade80" label="PROTEIN" />
              <MacroArc value={r(totals.carbs)}   goal={GOALS.carbs}   color={T.primary} label="CARBS" />
              <MacroArc value={r(totals.fat)}     goal={GOALS.fat}     color="#f87171" label="FAT" />
            </div>
          </div>

          {/* ── Micronutrient chips ── */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginTop: 12 }}>
            {[
              { label: "CALORIES", value: Math.round(totals.calories), goal: GOALS.calories, unit: "kcal" },
              { label: "FIBER", value: r(totals.fiber), goal: GOALS.fiber, unit: "g" },
              { label: "LOGGED", value: logged.length, goal: null, unit: "items" },
              { label: "REMAINING", value: calRemaining, goal: null, unit: "kcal" },
            ].map(({ label, value, goal, unit }) => (
              <div key={label} style={{ background: T.surface, borderRadius: 12,
                padding: "14px 16px", border: `1px solid rgba(255,255,255,0.03)` }}>
                <div style={{ fontFamily: T.fontB, fontSize: 9, fontWeight: 600,
                  letterSpacing: "0.12em", textTransform: "uppercase", color: T.dim, marginBottom: 6 }}>
                  {label}
                </div>
                <div style={{ fontFamily: T.fontD, fontSize: 22, fontWeight: 700, color: "#e8e6df", lineHeight: 1 }}>
                  {value.toLocaleString()}
                </div>
                <div style={{ fontFamily: T.fontB, fontSize: 10, color: T.dim, marginTop: 2 }}>
                  {goal ? `/ ${goal} ${unit}` : unit}
                </div>
                {goal && (
                  <div style={{ height: 2, background: T.cardHigh, borderRadius: 1, marginTop: 8, overflow: "hidden" }}>
                    <div style={{ width: `${Math.min(100, (value / goal) * 100)}%`, height: "100%",
                      background: `linear-gradient(90deg, ${T.primary}, ${T.primaryD})`,
                      transition: "width 0.8s ease" }} />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* ── Search ── */}
          <div style={{ marginTop: 32 }}>
            <h2 style={{ fontFamily: T.fontD, fontSize: 11, fontWeight: 700, letterSpacing: "0.14em",
              textTransform: "uppercase", color: T.dim, marginBottom: 14 }}>
              FOOD SEARCH
            </h2>

            <div style={{ position: "relative", marginBottom: 14 }}>
              <div style={{ position: "absolute", left: 16, top: "50%", transform: "translateY(-50%)",
                color: T.dim, fontSize: 15, pointerEvents: "none" }}>⌕</div>
              <input id="kl-search" value={query} onChange={handleInput}
                placeholder="Search any food — 'chicken breast', 'dal chapati', 'masala dosa'…"
                style={{
                  width: "100%", padding: "14px 48px 14px 44px", fontSize: 14,
                  borderRadius: 12, border: `1px solid rgba(0,212,170,${query ? "0.3" : "0.08"})`,
                  background: T.surface, color: "#e8e6df", boxSizing: "border-box",
                  fontFamily: T.fontB, outline: "none",
                  boxShadow: query ? `0 0 0 3px rgba(0,212,170,0.06)` : "none",
                  transition: "all 0.2s ease",
                }} />
              {loading && (
                <div style={{ position: "absolute", right: 16, top: "50%", transform: "translateY(-50%)" }}>
                  <div style={{ width: 16, height: 16, borderRadius: "50%",
                    border: `2px solid ${T.primary}`, borderTopColor: "transparent",
                    animation: "spin 0.7s linear infinite" }} />
                </div>
              )}
              {source && !loading && (
                <div style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)",
                  background: T.cardHigh, borderRadius: 5, padding: "2px 7px",
                  fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.08em",
                  color: T.primary }}>
                  {sourceBadge[source] || source.toUpperCase()}
                </div>
              )}
            </div>

            {error && (
              <div style={{ background: "rgba(255,180,171,0.08)", border: `1px solid rgba(255,180,171,0.2)`,
                borderRadius: 10, padding: "12px 16px", marginBottom: 14,
                fontFamily: T.fontB, fontSize: 13, color: T.error }}>
                ⚠ {error}
              </div>
            )}

            {/* Quick pills */}
            {!loading && results.length === 0 && !error && (
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.14em",
                  textTransform: "uppercase", color: T.dim, marginBottom: 10 }}>
                  QUICK SEARCH
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
                  {QUICK.map(q => (
                    <button key={q} onClick={() => { setQuery(q); doSearch(q); }}
                      style={{ padding: "6px 14px", borderRadius: 20,
                        fontFamily: T.fontD, fontSize: 11, fontWeight: 500,
                        cursor: "pointer", border: `1px solid rgba(200,198,198,0.12)`,
                        background: "transparent", color: T.silver,
                        letterSpacing: "0.03em", transition: "all 0.15s ease" }}
                      onMouseEnter={e => { e.target.style.borderColor = T.primary; e.target.style.color = T.primary; }}
                      onMouseLeave={e => { e.target.style.borderColor = "rgba(200,198,198,0.12)"; e.target.style.color = T.silver; }}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Results */}
            {results.length > 0 && (
              <div style={{ marginBottom: 28 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <div style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.14em",
                    textTransform: "uppercase", color: T.dim }}>
                    RESULTS — {results.length} FOODS
                  </div>
                  <button onClick={() => { setResults([]); setQuery(""); }}
                    style={{ background: "none", border: "none", color: T.dim, cursor: "pointer",
                      fontFamily: T.fontD, fontSize: 11 }}>✕ CLEAR</button>
                </div>
                {results.map((f, i) => <FoodCard key={i} food={f} onAdd={addFood} index={i} />)}
              </div>
            )}
          </div>

          {/* ── Logged today ── */}
          {logged.length > 0 && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                <h2 style={{ fontFamily: T.fontD, fontSize: 11, fontWeight: 700, letterSpacing: "0.14em",
                  textTransform: "uppercase", color: T.dim, margin: 0 }}>
                  LOGGED TODAY — {logged.length} ITEMS
                </h2>
                <button onClick={() => { setLogged([]); saveToday([]); }}
                  style={{ padding: "5px 12px", borderRadius: 7, fontFamily: T.fontD, fontSize: 10,
                    fontWeight: 600, letterSpacing: "0.06em", border: `1px solid rgba(255,180,171,0.2)`,
                    background: "transparent", color: "#ffb4ab", cursor: "pointer" }}>
                  CLEAR ALL
                </button>
              </div>
              <div style={{ background: T.surface, borderRadius: 16, overflow: "hidden" }}>
                {logged.map((item, idx) => (
                  <div key={item.id} style={{
                    display: "flex", alignItems: "center", gap: 12,
                    padding: "13px 18px",
                    borderBottom: idx < logged.length - 1 ? `1px solid rgba(255,255,255,0.04)` : "none",
                    transition: "background 0.15s ease",
                  }}
                    onMouseEnter={e => e.currentTarget.style.background = T.card}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                    <div style={{ width: 32, height: 32, borderRadius: 8, background: T.cardHigh,
                      display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                      <span style={{ fontSize: 14 }}>
                        {item.name.toLowerCase().includes("chicken") ? "🍗" :
                         item.name.toLowerCase().includes("egg") ? "🥚" :
                         item.name.toLowerCase().includes("rice") ? "🍚" :
                         item.name.toLowerCase().includes("dal") ? "🍲" :
                         item.name.toLowerCase().includes("protein") ? "💪" : "🥗"}
                      </span>
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontFamily: T.fontD, fontWeight: 600, fontSize: 13, color: "#e8e6df",
                        display: "flex", alignItems: "center", gap: 8 }}>
                        {item.name}
                        <span style={{ fontFamily: T.fontB, fontWeight: 400, fontSize: 11, color: T.dim }}>
                          {item.qty}g
                        </span>
                      </div>
                      <div style={{ fontFamily: T.fontB, fontSize: 11, color: T.dim, marginTop: 2 }}>
                        <span style={{ color: T.primary, fontWeight: 600 }}>{Math.round(item.calories)} kcal</span>
                        {" · "}{item.protein}g P · {item.carbs}g C · {item.fat}g F
                        {item.fiber > 0 ? ` · ${item.fiber}g fiber` : ""}
                      </div>
                    </div>
                    <button onClick={() => removeFood(item.id)}
                      style={{ background: "none", border: "none", cursor: "pointer",
                        fontSize: 14, color: T.dim, padding: "4px 6px", flexShrink: 0,
                        borderRadius: 6, transition: "color 0.15s" }}
                      onMouseEnter={e => e.target.style.color = T.error}
                      onMouseLeave={e => e.target.style.color = T.dim}>✕</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {logged.length === 0 && results.length === 0 && !loading && (
            <div style={{ textAlign: "center", padding: "60px 0" }}>
              <div style={{ fontSize: 40, marginBottom: 14 }}>⚡</div>
              <div style={{ fontFamily: T.fontD, fontSize: 13, fontWeight: 600,
                letterSpacing: "0.1em", textTransform: "uppercase", color: T.dim }}>
                START LOGGING YOUR FUEL
              </div>
              <div style={{ fontFamily: T.fontB, fontSize: 12, color: T.cardHigh === "#2a2a2a" ? "#555" : T.dim,
                marginTop: 6 }}>
                Search above to track your nutrition
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
