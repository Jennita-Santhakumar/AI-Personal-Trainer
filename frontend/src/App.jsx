import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import api from "./services/api";
import Dashboard    from "./components/dashboard/Dashboard";
import CoachChat    from "./components/coach/CoachChat";
import PlanPage     from "./pages/PlanPage";
import BadgesPage   from "./pages/BadgesPage";
import ProfilePage  from "./pages/ProfilePage";
import FormPage     from "./pages/FormPage";
import PoseDetectionPage from "./pages/PoseDetectionPage";
import NutritionPage    from "./pages/NutritionPage";

const KL_STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Lexend:wght@300;400;500;600&display=swap');
  *, *::before, *::after { box-sizing: border-box; }
  :root {
    --kl-bg: #131313; --kl-surface: #1c1b1b; --kl-card: #201f1f; --kl-card-high: #2a2a2a;
    --kl-primary: #00d4aa; --kl-primary-d: #00b896; --kl-silver: #c8c6c6;
    --kl-dim: #888580; --kl-text: #e8e6df; --kl-error: #ffb4ab;
    --kl-font-d: 'Space Grotesk', sans-serif; --kl-font-b: 'Lexend', sans-serif;
    --color-background-primary: #1c1b1b; --color-background-secondary: #201f1f;
    --color-background-tertiary: #131313; --color-background-info: #042c53;
    --color-background-success: #173404; --color-background-warning: #412402;
    --color-background-danger: #501313; --color-text-primary: #e8e6df;
    --color-text-secondary: #c8c6c6; --color-text-tertiary: #888580;
    --color-text-info: #85b7eb; --color-text-success: #97c459;
    --color-text-warning: #00d4aa; --color-text-danger: #ffb4ab;
    --color-border-tertiary: rgba(255,255,255,0.05);
    --color-border-secondary: rgba(255,255,255,0.1);
  }
  html, body { margin: 0; padding: 0; background: #131313 !important; color: #e8e6df !important; font-family: 'Lexend', sans-serif; -webkit-font-smoothing: antialiased; }
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: #131313; }
  ::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 2px; }
  input, textarea, select { font-family: 'Lexend', sans-serif; }
  input[type="range"] { -webkit-appearance: none; background: #2a2a2a; height: 4px; border-radius: 2px; outline: none; }
  input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 16px; height: 16px; border-radius: 50%; background: linear-gradient(135deg, #00d4aa, #00b896); cursor: pointer; }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes kl-pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(0,212,170,0.4); } 50% { box-shadow: 0 0 0 10px rgba(0,212,170,0); } }
  @keyframes slideIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes bounce { 0%,80%,100% { transform: translateY(0); opacity: .4; } 40% { transform: translateY(-4px); opacity: 1; } }
`;

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("demo@fitnessplatform.com");
  const [password, setPassword] = useState("Demo1234!");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("login");
  const inp = { display:"block", width:"100%", marginTop:6, padding:"12px 14px", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, background:"#131313", color:"#e8e6df", fontSize:14, outline:"none", fontFamily:"'Lexend',sans-serif" };
  const submit = async (e) => {
    e.preventDefault(); setLoading(true); setError("");
    try {
      const res = mode==="register"
        ? await api.register({ email, password, name, goal:"strength", level:"beginner", age:25, weight_kg:70, height_cm:175 })
        : await api.login(email, password);
      api.setToken(res.access_token); onLogin(res);
    } catch(err) { setError(err.message); }
    setLoading(false);
  };
  return (
    <div style={{ minHeight:"100vh", background:"#131313", display:"flex", alignItems:"center", justifyContent:"center", padding:"2rem" }}>
      <div style={{ width:"100%", maxWidth:400 }}>
        <div style={{ marginBottom:36 }}>
          <div style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:11, fontWeight:700, letterSpacing:"0.2em", color:"#00d4aa", marginBottom:14, textTransform:"uppercase" }}>ALL FIT</div>
          <h1 style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:"clamp(28px,5vw,42px)", fontWeight:700, letterSpacing:"-0.02em", color:"#e8e6df", margin:0, lineHeight:1 }}>
            ELITE TRAINING<br/><span style={{ color:"transparent", WebkitTextStroke:"1px #888580" }}>INTELLIGENCE</span>
          </h1>
        </div>
        <div style={{ background:"#1c1b1b", borderRadius:16, padding:"28px" }}>
          <div style={{ display:"flex", gap:4, marginBottom:24, background:"#131313", borderRadius:10, padding:4 }}>
            {["login","register"].map(m => (
              <button key={m} onClick={() => setMode(m)} style={{ flex:1, padding:"8px", borderRadius:8, border:"none", cursor:"pointer", background:mode===m?"linear-gradient(135deg,#00d4aa,#00b896)":"transparent", color:mode===m?"#131313":"#888580", fontFamily:"'Space Grotesk',sans-serif", fontSize:11, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", transition:"all 0.2s" }}>{m}</button>
            ))}
          </div>
          <form onSubmit={submit} style={{ display:"flex", flexDirection:"column", gap:14 }}>
            {mode==="register" && <div><label style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:10, fontWeight:700, letterSpacing:"0.12em", textTransform:"uppercase", color:"#888580" }}>Name</label><input value={name} onChange={e=>setName(e.target.value)} style={inp} /></div>}
            <div><label style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:10, fontWeight:700, letterSpacing:"0.12em", textTransform:"uppercase", color:"#888580" }}>Email</label><input value={email} onChange={e=>setEmail(e.target.value)} type="email" style={inp} /></div>
            <div><label style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:10, fontWeight:700, letterSpacing:"0.12em", textTransform:"uppercase", color:"#888580" }}>Password</label><input value={password} onChange={e=>setPassword(e.target.value)} type="password" style={inp} /></div>
            {error && <div style={{ background:"rgba(255,180,171,0.08)", border:"1px solid rgba(255,180,171,0.2)", borderRadius:8, padding:"10px 14px", fontFamily:"'Lexend',sans-serif", fontSize:13, color:"#ffb4ab" }}>⚠ {error}</div>}
            <button type="submit" disabled={loading} style={{ marginTop:4, padding:"13px", borderRadius:10, border:"none", background:loading?"#2a2a2a":"linear-gradient(135deg,#00d4aa,#00b896)", color:loading?"#888580":"#131313", fontFamily:"'Space Grotesk',sans-serif", fontSize:12, fontWeight:700, letterSpacing:"0.1em", cursor:loading?"not-allowed":"pointer", textTransform:"uppercase" }}>
              {loading?"PLEASE WAIT…":mode==="login"?"SIGN IN":"CREATE ACCOUNT"}
            </button>
          </form>
          {mode==="login" && <p style={{ textAlign:"center", fontFamily:"'Lexend',sans-serif", fontSize:11, color:"#888580", marginTop:14, marginBottom:0 }}>demo@fitnessplatform.com / Demo1234!</p>}
        </div>
      </div>
    </div>
  );
}

function NavBar({ user, onLogout }) {
  const loc = useLocation();
  const links = [
    { to:"/",          label:"ROADMAP"   },
    { to:"/coach",     label:"AI COACH"  },
    { to:"/pose",      label:"FORM AI"   },
    { to:"/nutrition", label:"NUTRITION" },
    { to:"/plan",      label:"MY PLAN"   },
    { to:"/badges",    label:"BADGES"    },
    { to:"/profile",   label:"PROFILE"   },
  ];
  return (
    <nav style={{ position:"sticky", top:0, zIndex:100, background:"rgba(19,19,19,0.9)", backdropFilter:"blur(20px)", borderBottom:"1px solid rgba(255,255,255,0.04)", padding:"0 28px", display:"flex", alignItems:"center", height:56 }}>
      <Link to="/" style={{ textDecoration:"none", flexShrink:0, marginRight:28 }}>
        <span style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:11, fontWeight:700, letterSpacing:"0.2em", color:"#00d4aa", textTransform:"uppercase" }}>ALL FIT</span>
      </Link>
      <div style={{ display:"flex", alignItems:"center", gap:2, flex:1, overflowX:"auto" }}>
        {links.map(l => {
          const active = loc.pathname === l.to;
          return (
            <Link key={l.to} to={l.to} style={{ textDecoration:"none", flexShrink:0, fontFamily:"'Space Grotesk',sans-serif", fontSize:11, fontWeight:active?700:500, letterSpacing:"0.1em", color:active?"#00d4aa":"#888580", padding:"5px 14px", borderRadius:6, background:active?"rgba(0,212,170,0.06)":"transparent", borderBottom:active?"1px solid #00d4aa":"1px solid transparent", transition:"all 0.15s" }}>{l.label}</Link>
          );
        })}
      </div>
      <div style={{ display:"flex", alignItems:"center", gap:10, flexShrink:0 }}>
        <div style={{ width:30, height:30, borderRadius:"50%", background:"linear-gradient(135deg,#00d4aa,#00b896)", display:"flex", alignItems:"center", justifyContent:"center", fontFamily:"'Space Grotesk',sans-serif", fontSize:12, fontWeight:700, color:"#131313" }}>
          {(user?.name||"U")[0].toUpperCase()}
        </div>
        <button onClick={onLogout} style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:10, fontWeight:700, letterSpacing:"0.1em", padding:"5px 12px", borderRadius:7, border:"1px solid rgba(255,255,255,0.08)", background:"transparent", color:"#888580", cursor:"pointer", textTransform:"uppercase" }}>OUT</button>
      </div>
    </nav>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) { api.getMe().then(setUser).catch(() => api.clearToken()).finally(() => setChecking(false)); }
    else setChecking(false);
  }, []);
  if (checking) return (
    <><style>{KL_STYLES}</style>
    <div style={{ minHeight:"100vh", background:"#131313", display:"flex", alignItems:"center", justifyContent:"center" }}>
      <div style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:11, letterSpacing:"0.2em", color:"#888580", textTransform:"uppercase" }}>INITIALIZING…</div>
    </div></>
  );
  const handleLogin = (res) => setUser({ id:res.user_id, name:res.name });
  const handleLogout = () => { api.clearToken(); setUser(null); };
  return (
    <><style>{KL_STYLES}</style>
    <BrowserRouter>
      {!user ? <LoginPage onLogin={handleLogin} /> : (
        <>
          <NavBar user={user} onLogout={handleLogout} />
          <Routes>
            <Route path="/"          element={<Dashboard />} />
            <Route path="/coach"     element={<div style={{ height:"calc(100vh - 56px)" }}><CoachChat /></div>} />
            <Route path="/pose"      element={<PoseDetectionPage />} />
            <Route path="/nutrition" element={<NutritionPage />} />
            <Route path="/plan"      element={<PlanPage />} />
            <Route path="/badges"    element={<BadgesPage />} />
            <Route path="/form"      element={<FormPage />} />
            <Route path="/profile"   element={<ProfilePage />} />
            <Route path="*"          element={<Navigate to="/" />} />
          </Routes>
        </>
      )}
    </BrowserRouter></>
  );
}
