import React, { useState, useEffect } from "react";
import api from "../services/api";
import PlanGenerator from "../components/workout/PlanGenerator";
import PlanViewer from "../components/workout/PlanViewer";

const T = { bg:"#131313", surface:"#1c1b1b", card:"#201f1f", primary:"#00d4aa", primaryD:"#00b896", dim:"#888580", text:"#e8e6df", fontD:"'Space Grotesk',sans-serif", fontB:"'Lexend',sans-serif" };

export default function PlanPage(){
  const[plan,setPlan]=useState(null);
  const[loading,setLoading]=useState(true);
  const[showGenerator,setShowGenerator]=useState(false);

  useEffect(()=>{ api.getCurrentPlan().then(setPlan).catch(()=>setPlan(null)).finally(()=>setLoading(false)); },[]);

  const handleGenerated=(res)=>{ setPlan(res); setShowGenerator(false); };

  if(loading) return(
    <div style={{ minHeight:"60vh", display:"flex", alignItems:"center", justifyContent:"center" }}>
      <div style={{ width:28, height:28, borderRadius:"50%", border:`2px solid #00d4aa`, borderTopColor:"transparent", animation:"spin 0.8s linear infinite" }}/>
    </div>
  );

  if(showGenerator) return(
    <div>
      <div style={{ padding:"20px 28px", borderBottom:"1px solid rgba(255,255,255,0.04)", display:"flex", alignItems:"center", gap:16 }}>
        <button onClick={()=>setShowGenerator(false)} style={{ fontFamily:T.fontD, fontSize:11, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", background:"transparent", border:"none", cursor:"pointer", color:T.dim }}>← BACK</button>
        <span style={{ fontFamily:T.fontD, fontSize:13, fontWeight:700, letterSpacing:"0.08em", textTransform:"uppercase", color:T.text }}>GENERATE NEW PLAN</span>
      </div>
      <PlanGenerator onPlanGenerated={handleGenerated}/>
    </div>
  );

  if(!plan) return(
    <div style={{ minHeight:"70vh", display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:20, textAlign:"center", padding:"2rem" }}>
      <div style={{ fontSize:48 }}>🏋️</div>
      <div style={{ fontFamily:T.fontD, fontSize:"clamp(22px,4vw,36px)", fontWeight:700, letterSpacing:"-0.01em", color:T.text }}>NO ACTIVE PLAN</div>
      <p style={{ fontFamily:T.fontB, fontSize:14, color:T.dim, maxWidth:360, lineHeight:1.7 }}>Generate a personalised workout plan based on your goal, experience, and schedule.</p>
      <button onClick={()=>setShowGenerator(true)} style={{ padding:"13px 28px", borderRadius:10, border:"none", background:`linear-gradient(135deg,#00d4aa,#00b896)`, color:"#131313", fontFamily:T.fontD, fontSize:12, fontWeight:700, letterSpacing:"0.1em", cursor:"pointer", textTransform:"uppercase" }}>
        GENERATE MY PLAN
      </button>
    </div>
  );

  return(
    <div>
      <div style={{ padding:"20px 28px", borderBottom:"1px solid rgba(255,255,255,0.04)", display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div>
          <div style={{ fontFamily:T.fontD, fontSize:10, fontWeight:700, letterSpacing:"0.18em", textTransform:"uppercase", color:T.primary, marginBottom:4 }}>ACTIVE PLAN</div>
          <div style={{ fontFamily:T.fontB, fontSize:12, color:T.dim }}>Created {new Date(plan.created_at).toLocaleDateString()}</div>
        </div>
        <button onClick={()=>setShowGenerator(true)} style={{ fontFamily:T.fontD, fontSize:10, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", padding:"8px 16px", borderRadius:9, border:"1px solid rgba(255,255,255,0.08)", background:"transparent", color:T.dim, cursor:"pointer" }}>
          NEW PLAN
        </button>
      </div>
      <PlanViewer plan={plan}/>
    </div>
  );
}
