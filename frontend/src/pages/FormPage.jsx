/**
 * frontend/src/pages/FormPage.jsx
 * Interactive form correction guide for all workout types.
 */
import React, { useState, useEffect } from "react";
import api from "../services/api";

const CATEGORY_MAP = {
  "Barbell / Powerlifting": ["squat","bench","deadlift","overhead_press","row","pull_up"],
  "Running & Cardio":       ["running","easy_run","hiit","cycling"],
  "Bodyweight":             ["push_up","plank","lunge"],
  "Yoga & Flexibility":     ["yoga"],
  "Olympic / Functional":   ["clean","kettlebell_swing"],
  "Swimming":               ["swimming"],
};

const CATEGORY_ICONS = {
  "Barbell / Powerlifting": "🏋️",
  "Running & Cardio":       "🏃",
  "Bodyweight":             "💪",
  "Yoga & Flexibility":     "🧘",
  "Olympic / Functional":   "⚡",
  "Swimming":               "🏊",
};

const ACTIVITY_LABELS = {
  squat:"Squat", bench:"Bench Press", deadlift:"Deadlift",
  overhead_press:"Overhead Press", row:"Barbell Row", pull_up:"Pull-up",
  running:"Running", easy_run:"Easy Run", hiit:"HIIT",
  cycling:"Cycling", push_up:"Push-up", plank:"Plank",
  lunge:"Lunge", yoga:"Yoga", clean:"Power Clean",
  kettlebell_swing:"Kettlebell Swing", swimming:"Swimming",
};

function Section({ title, color, children }) {
  return (
    <div style={{ marginBottom:16 }}>
      <div style={{ fontSize:11, fontWeight:600, textTransform:"uppercase",
        letterSpacing:"0.06em", color, marginBottom:8 }}>{title}</div>
      {children}
    </div>
  );
}

function Pill({ text, color = "var(--color-text-secondary)", bg = "var(--color-background-secondary)" }) {
  return (
    <div style={{ fontSize:13, padding:"7px 12px", borderRadius:8,
      background:bg, color, lineHeight:1.5, marginBottom:6,
      border:"0.5px solid var(--color-border-tertiary)" }}>
      {text}
    </div>
  );
}

function MistakeCard({ mistake, why, fix }) {
  const [open, setOpen] = useState(false);
  return (
    <div onClick={() => setOpen(o=>!o)}
      style={{ borderRadius:10, border:"0.5px solid var(--color-border-secondary)",
        overflow:"hidden", marginBottom:8, cursor:"pointer" }}>
      <div style={{ padding:"10px 14px", display:"flex", justifyContent:"space-between",
        alignItems:"center", background:"var(--color-background-danger)" }}>
        <span style={{ fontSize:13, fontWeight:500, color:"var(--color-text-danger)" }}>
          ⚠ {mistake}
        </span>
        <span style={{ fontSize:12, color:"var(--color-text-tertiary)" }}>{open?"▲":"▼"}</span>
      </div>
      {open && (
        <div style={{ padding:"12px 14px", background:"var(--color-background-primary)",
          display:"flex", flexDirection:"column", gap:10 }}>
          <div>
            <div style={{ fontSize:11, fontWeight:600, color:"var(--color-text-tertiary)",
              textTransform:"uppercase", letterSpacing:"0.05em", marginBottom:4 }}>Why it happens</div>
            <div style={{ fontSize:13, color:"var(--color-text-secondary)", lineHeight:1.6 }}>{why}</div>
          </div>
          <div>
            <div style={{ fontSize:11, fontWeight:600, color:"var(--color-text-success)",
              textTransform:"uppercase", letterSpacing:"0.05em", marginBottom:4 }}>The fix</div>
            <div style={{ fontSize:13, color:"var(--color-text-primary)", lineHeight:1.6 }}>{fix}</div>
          </div>
        </div>
      )}
    </div>
  );
}

function FormDetail({ activity, data, onBack }) {
  return (
    <div style={{ padding:"1.5rem", maxWidth:720, margin:"0 auto" }}>
      <button onClick={onBack} style={{ background:"none", border:"none", cursor:"pointer",
        color:"var(--color-text-secondary)", fontSize:14, marginBottom:16,
        display:"flex", alignItems:"center", gap:6, padding:0 }}>
        ← Back
      </button>

      <h2 style={{ fontSize:22, fontWeight:600, marginBottom:4 }}>
        {ACTIVITY_LABELS[activity] || activity}
      </h2>
      <p style={{ fontSize:13, color:"var(--color-text-secondary)", marginBottom:20 }}>
        Form guide — cues, mistakes & fixes
      </p>

      {/* Coaching cues */}
      <Section title="🎯 Key coaching cues" color="#534AB7">
        {data.cues?.map((c,i) => <Pill key={i} text={c} />)}
      </Section>

      {/* Common mistakes — expandable */}
      <Section title="⚠ Common mistakes (tap to expand)" color="var(--color-text-danger)">
        {data.common_mistakes?.map((m,i) => (
          <MistakeCard key={i} mistake={m.mistake} why={m.why} fix={m.fix} />
        ))}
      </Section>

      {/* Injury risks */}
      <Section title="🚨 Injury risks if uncorrected" color="var(--color-text-warning)">
        <div style={{ display:"flex", flexWrap:"wrap", gap:6 }}>
          {data.injury_risks?.map((r,i) => (
            <span key={i} style={{ fontSize:12, padding:"4px 10px", borderRadius:20,
              background:"var(--color-background-warning)",
              color:"var(--color-text-warning)", fontWeight:500 }}>{r}</span>
          ))}
        </div>
      </Section>

      {/* Warmup drills */}
      {data.warmup_drills?.length > 0 && (
        <Section title="🔥 Warmup drills" color="var(--color-text-success)">
          {data.warmup_drills.map((d,i) => (
            <Pill key={i} text={`${i+1}. ${d}`}
              bg="var(--color-background-success)" color="var(--color-text-success)" />
          ))}
        </Section>
      )}

      {/* Self check */}
      {data.self_check && (
        <Section title="📱 How to self-check with your phone" color="var(--color-text-info)">
          <div style={{ fontSize:13, padding:"12px 14px", borderRadius:10,
            background:"var(--color-background-info)", color:"var(--color-text-info)",
            lineHeight:1.7, border:"0.5px solid var(--color-border-tertiary)" }}>
            {data.self_check}
          </div>
        </Section>
      )}
    </div>
  );
}

export default function FormPage() {
  const [selected, setSelected]   = useState(null);
  const [formData, setFormData]   = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState("");
  const [search, setSearch]       = useState("");

  const handleSelect = async (activity) => {
    setLoading(true); setError("");
    try {
      const data = await api._fetch(`/api/v1/form/${activity}`);
      setFormData(data);
      setSelected(activity);
    } catch(e) { setError(e.message); }
    setLoading(false);
  };

  const filteredCategories = Object.entries(CATEGORY_MAP).map(([cat, activities]) => ({
    cat,
    activities: activities.filter(a =>
      !search || (ACTIVITY_LABELS[a]||a).toLowerCase().includes(search.toLowerCase())
    )
  })).filter(c => c.activities.length > 0);

  if (loading) return (
    <div style={{ padding:"3rem", textAlign:"center", color:"var(--color-text-secondary)" }}>
      Loading form guide…
    </div>
  );

  if (selected && formData) return (
    <FormDetail activity={selected} data={formData} onBack={() => { setSelected(null); setFormData(null); }} />
  );

  return (
    <div style={{ padding:"1.5rem", maxWidth:800, margin:"0 auto" }}>
      <h2 style={{ fontSize:20, fontWeight:600, marginBottom:4 }}>Form Corrections</h2>
      <p style={{ fontSize:13, color:"var(--color-text-secondary)", marginBottom:20 }}>
        Coaching cues, common mistakes and fixes for every workout.
      </p>

      {/* Search */}
      <input
        value={search}
        onChange={e => setSearch(e.target.value)}
        placeholder="Search exercises…"
        style={{ width:"100%", padding:"9px 14px", fontSize:14, borderRadius:10, marginBottom:20,
          border:"0.5px solid var(--color-border-secondary)",
          background:"var(--color-background-primary)",
          color:"var(--color-text-primary)", boxSizing:"border-box" }}
      />

      {error && <div style={{ color:"var(--color-text-danger)", marginBottom:12, fontSize:13 }}>{error}</div>}

      {filteredCategories.map(({ cat, activities }) => (
        <div key={cat} style={{ marginBottom:24 }}>
          <div style={{ fontSize:13, fontWeight:600, color:"var(--color-text-secondary)",
            marginBottom:10, display:"flex", alignItems:"center", gap:6 }}>
            {CATEGORY_ICONS[cat]} {cat}
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(160px,1fr))", gap:8 }}>
            {activities.map(a => (
              <button key={a} onClick={() => handleSelect(a)}
                style={{ padding:"14px 12px", borderRadius:12, border:"0.5px solid var(--color-border-secondary)",
                  background:"var(--color-background-primary)",
                  color:"var(--color-text-primary)", cursor:"pointer", fontSize:13, fontWeight:500,
                  textAlign:"left", transition:"background 0.15s, border-color 0.15s" }}
                onMouseEnter={e => { e.currentTarget.style.background="var(--color-background-secondary)"; e.currentTarget.style.borderColor="#534AB7"; }}
                onMouseLeave={e => { e.currentTarget.style.background="var(--color-background-primary)"; e.currentTarget.style.borderColor="var(--color-border-secondary)"; }}>
                {ACTIVITY_LABELS[a] || a}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
