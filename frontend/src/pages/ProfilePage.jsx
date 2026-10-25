/**
 * ProfilePage.jsx — All Fit Design System
 */
import React, { useState, useEffect } from "react";
import api from "../services/api";

const T = {
  bg:"#131313", surface:"#1c1b1b", card:"#201f1f", cardHigh:"#2a2a2a",
  primary:"#00d4aa", primaryD:"#00b896", silver:"#c8c6c6", dim:"#888580",
  text:"#e8e6df", error:"#ffb4ab", success:"#97c459",
  fontD:"'Space Grotesk',sans-serif", fontB:"'Lexend',sans-serif",
};

const inp = {
  fontSize:13, padding:"10px 12px", border:"1px solid rgba(255,255,255,0.07)",
  borderRadius:9, background:T.bg, color:T.text, width:"100%",
  boxSizing:"border-box", fontFamily:T.fontB, outline:"none",
};

export default function ProfilePage() {
  const [stats, setStats]       = useState(null);
  const [wearables, setWearables] = useState(null);
  const [editing, setEditing]   = useState(false);
  const [form, setForm]         = useState({});
  const [saving, setSaving]     = useState(false);
  const [msg, setMsg]           = useState("");

  useEffect(() => {
    api._fetch("/api/v1/users/me/stats").then(setStats).catch(() => {});
    api._fetch("/api/v1/wearables/connected").then(setWearables).catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api._fetch("/api/v1/users/me", { method:"PATCH", body:JSON.stringify(form) });
      setMsg("Profile updated.");
      setEditing(false);
      const updated = await api._fetch("/api/v1/users/me/stats");
      setStats(updated);
    } catch(e) { setMsg(`Error: ${e.message}`); }
    setSaving(false);
  };

  const connectWearable = async (provider) => {
    const res = await api._fetch(`/api/v1/wearables/${provider}/connect`);
    if (res.auth_url) window.open(res.auth_url, "_blank");
  };

  const disconnectWearable = async (provider) => {
    await api._fetch(`/api/v1/wearables/${provider}/disconnect`, { method:"DELETE" });
    setWearables(w => ({ ...w, [provider]:{ connected:false } }));
  };

  if (!stats) return (
    <div style={{ minHeight:"60vh", display:"flex", alignItems:"center", justifyContent:"center" }}>
      <div style={{ width:28, height:28, borderRadius:"50%", border:`2px solid ${T.primary}`, borderTopColor:"transparent", animation:"spin 0.8s linear infinite" }}/>
    </div>
  );

  const { profile, stats:s, gamification:g } = stats;

  return (
    <div style={{ padding:"28px", maxWidth:700, margin:"0 auto" }}>

      {/* Header */}
      <div style={{ marginBottom:28 }}>
        <div style={{ fontFamily:T.fontD, fontSize:10, fontWeight:700, letterSpacing:"0.18em", textTransform:"uppercase", color:T.primary, marginBottom:10 }}>ACCOUNT</div>
        <h1 style={{ fontFamily:T.fontD, fontSize:"clamp(24px,4vw,42px)", fontWeight:700, letterSpacing:"-0.02em", color:T.text, margin:0, lineHeight:1 }}>YOUR PROFILE</h1>
      </div>

      {/* Profile card */}
      <div style={{ background:T.surface, borderRadius:16, padding:"24px", marginBottom:12 }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:20 }}>
          <div style={{ display:"flex", alignItems:"center", gap:14 }}>
            <div style={{ width:52, height:52, borderRadius:"50%", background:`linear-gradient(135deg,${T.primary},${T.primaryD})`, display:"flex", alignItems:"center", justifyContent:"center", fontFamily:T.fontD, fontSize:20, fontWeight:700, color:"#131313" }}>
              {(profile.name || "?")[0].toUpperCase()}
            </div>
            <div>
              <div style={{ fontFamily:T.fontD, fontSize:16, fontWeight:700, color:T.text }}>{profile.name}</div>
              <div style={{ fontFamily:T.fontB, fontSize:12, color:T.dim, marginTop:2, textTransform:"capitalize" }}>{profile.goal} · {profile.level}</div>
            </div>
          </div>
          <button onClick={() => { setEditing(e => !e); setForm(profile); }} style={{
            fontFamily:T.fontD, fontSize:10, fontWeight:700, letterSpacing:"0.1em",
            padding:"6px 14px", borderRadius:8, border:"1px solid rgba(255,255,255,0.08)",
            background:"transparent", color:T.dim, cursor:"pointer", textTransform:"uppercase"
          }}>{editing ? "CANCEL" : "EDIT"}</button>
        </div>

        {editing ? (
          <div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:12 }}>
              {[["name","Full Name"],["age","Age"],["weight_kg","Weight (kg)"],["height_cm","Height (cm)"]].map(([k,label]) => (
                <div key={k}>
                  <label style={{ fontFamily:T.fontD, fontSize:9, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:T.dim, display:"block", marginBottom:5 }}>{label}</label>
                  <input value={form[k]||""} onChange={e => setForm(f => ({...f,[k]:e.target.value}))} style={inp}/>
                </div>
              ))}
            </div>
            {msg && <div style={{ fontFamily:T.fontB, fontSize:13, color:msg.startsWith("Error") ? T.error : T.success, marginBottom:10 }}>{msg}</div>}
            <button onClick={handleSave} disabled={saving} style={{
              width:"100%", padding:"12px", borderRadius:10, border:"none",
              background:saving ? T.card : `linear-gradient(135deg,${T.primary},${T.primaryD})`,
              color:saving ? T.dim : "#131313", fontFamily:T.fontD, fontSize:12, fontWeight:700,
              letterSpacing:"0.08em", textTransform:"uppercase", cursor:saving ? "not-allowed" : "pointer"
            }}>{saving ? "SAVING…" : "SAVE CHANGES"}</button>
          </div>
        ) : (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
            {[
              ["AGE",     profile.age       ? `${profile.age} yrs`       : "—"],
              ["WEIGHT",  profile.weight_kg ? `${profile.weight_kg} kg`  : "—"],
              ["HEIGHT",  profile.height_cm ? `${profile.height_cm} cm`  : "—"],
              ["INJURIES",(profile.injuries||[]).join(", ") || "None"],
            ].map(([k,v]) => (
              <div key={k} style={{ background:T.card, borderRadius:10, padding:"12px 14px" }}>
                <div style={{ fontFamily:T.fontD, fontSize:9, fontWeight:700, letterSpacing:"0.12em", textTransform:"uppercase", color:T.dim, marginBottom:5 }}>{k}</div>
                <div style={{ fontFamily:T.fontB, fontSize:14, color:T.silver }}>{v}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stats */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:10, marginBottom:12 }}>
        {[
          ["SESSIONS",  s.total_sessions],
          ["LEVEL",     g.level || "Beginner"],
          ["STREAK",    `${g.streak || 0}d`],
        ].map(([label,val]) => (
          <div key={label} style={{ background:T.surface, borderRadius:14, padding:"18px 20px" }}>
            <div style={{ fontFamily:T.fontD, fontSize:9, fontWeight:700, letterSpacing:"0.14em", textTransform:"uppercase", color:T.dim, marginBottom:6 }}>{label}</div>
            <div style={{ fontFamily:T.fontD, fontSize:26, fontWeight:700, background:`linear-gradient(135deg,${T.primary},${T.primaryD})`, WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent" }}>{val}</div>
          </div>
        ))}
      </div>

      {/* Personal Records */}
      {Object.keys(s.personal_records || {}).length > 0 && (
        <div style={{ background:T.surface, borderRadius:14, padding:"22px 24px", marginBottom:12 }}>
          <div style={{ fontFamily:T.fontD, fontSize:9, fontWeight:700, letterSpacing:"0.14em", textTransform:"uppercase", color:T.dim, marginBottom:14 }}>PERSONAL RECORDS</div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(120px,1fr))", gap:8 }}>
            {Object.entries(s.personal_records).map(([lift,val]) => (
              <div key={lift} style={{ background:T.card, borderRadius:10, padding:"12px", textAlign:"center" }}>
                <div style={{ fontFamily:T.fontD, fontSize:9, fontWeight:700, letterSpacing:"0.1em", textTransform:"capitalize", color:T.dim, marginBottom:6 }}>{lift}</div>
                <div style={{ fontFamily:T.fontD, fontSize:20, fontWeight:700, color:T.primary }}>{val}<span style={{ fontSize:11, color:T.dim, marginLeft:2 }}>kg</span></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Wearable connections */}
      <div style={{ background:T.surface, borderRadius:14, padding:"22px 24px" }}>
        <div style={{ fontFamily:T.fontD, fontSize:9, fontWeight:700, letterSpacing:"0.14em", textTransform:"uppercase", color:T.dim, marginBottom:16 }}>CONNECTED DEVICES</div>
        {[
          { id:"fitbit",     label:"Fitbit",       desc:"Steps, HR, calories, sleep" },
          { id:"google_fit", label:"Google Fit",   desc:"Activity, heart rate" },
          { id:"apple",      label:"Apple Health", desc:"Coming soon" },
        ].map((w,i,arr) => {
          const connected = wearables?.[w.id]?.connected;
          return (
            <div key={w.id} style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"14px 0", borderBottom: i < arr.length-1 ? "1px solid rgba(255,255,255,0.04)" : "none" }}>
              <div>
                <div style={{ fontFamily:T.fontD, fontSize:13, fontWeight:600, color:T.silver }}>{w.label}</div>
                <div style={{ fontFamily:T.fontB, fontSize:11, color:T.dim, marginTop:2 }}>{w.desc}</div>
              </div>
              {w.id === "apple" ? (
                <span style={{ fontFamily:T.fontD, fontSize:10, fontWeight:700, letterSpacing:"0.08em", color:T.dim }}>SOON</span>
              ) : connected ? (
                <div style={{ display:"flex", gap:10, alignItems:"center" }}>
                  <span style={{ fontFamily:T.fontD, fontSize:10, fontWeight:700, color:T.success, letterSpacing:"0.08em" }}>● CONNECTED</span>
                  <button onClick={() => disconnectWearable(w.id)} style={{ fontFamily:T.fontD, fontSize:10, fontWeight:700, letterSpacing:"0.08em", padding:"5px 12px", borderRadius:7, border:`1px solid rgba(255,180,171,0.3)`, background:"transparent", color:T.error, cursor:"pointer", textTransform:"uppercase" }}>DISCONNECT</button>
                </div>
              ) : (
                <button onClick={() => connectWearable(w.id)} style={{ fontFamily:T.fontD, fontSize:10, fontWeight:700, letterSpacing:"0.08em", padding:"7px 16px", borderRadius:8, border:"none", background:`linear-gradient(135deg,${T.primary},${T.primaryD})`, color:"#131313", cursor:"pointer", textTransform:"uppercase" }}>CONNECT</button>
              )}
            </div>
          );
        })}
      </div>

    </div>
  );
}
