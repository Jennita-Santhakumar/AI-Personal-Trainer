import React, { useState } from "react";
import api from "../../services/api";

const T = { bg:"#131313", surface:"#1c1b1b", card:"#201f1f", cardHigh:"#2a2a2a", primary:"#00d4aa", primaryD:"#00b896", silver:"#c8c6c6", dim:"#888580", text:"#e8e6df", error:"#ffb4ab", fontD:"'Space Grotesk',sans-serif", fontB:"'Lexend',sans-serif" };

const GOALS = [
  { value:"strength",    label:"STRENGTH",    desc:"Build maximal strength — powerlifting focus" },
  { value:"fat_loss",    label:"FAT LOSS",    desc:"Lose fat, preserve muscle — circuits + cardio" },
  { value:"endurance",   label:"ENDURANCE",   desc:"Running performance — aerobic base + speed" },
  { value:"flexibility", label:"FLEXIBILITY", desc:"Mobility & recovery — yoga focus" },
  { value:"hybrid",      label:"HYBRID",      desc:"Balanced — lifting + cardio + recovery" },
];
const LEVELS = [
  { value:"beginner",     label:"BEGINNER",     desc:"< 1 year consistent training" },
  { value:"intermediate", label:"INTERMEDIATE", desc:"1–3 years, good technique" },
  { value:"advanced",     label:"ADVANCED",     desc:"3+ years, competition level" },
];
const COMMON_INJURIES = ["lower_back","knee","shoulder","ankle","wrist"];

export default function PlanGenerator({onPlanGenerated}){
  const[form,setForm]=useState({ goal:"strength", level:"intermediate", days_per_week:4, injuries:[], sport_focus:"general", weeks:4, current_maxes:{squat:"",bench:"",deadlift:""} });
  const[loading,setLoading]=useState(false);
  const[error,setError]=useState("");

  const toggleInjury=(inj)=>setForm(f=>({...f,injuries:f.injuries.includes(inj)?f.injuries.filter(i=>i!==inj):[...f.injuries,inj]}));

  const handleSubmit=async(e)=>{
    e.preventDefault(); setLoading(true); setError("");
    try{
      const maxes={};
      for(const[k,v] of Object.entries(form.current_maxes)){if(v)maxes[k]=parseFloat(v);}
      const res=await api.generatePlan({...form,current_maxes:maxes});
      onPlanGenerated?.(res);
    }catch(err){setError(err.message);}
    setLoading(false);
  };

  const inp={fontSize:13,padding:"10px 14px",border:"1px solid rgba(255,255,255,0.07)",borderRadius:9,background:T.bg,color:T.text,width:"100%",fontFamily:T.fontB,outline:"none"};
  const label={fontFamily:T.fontD,fontSize:9,fontWeight:700,letterSpacing:"0.14em",textTransform:"uppercase",color:T.dim,display:"block",marginBottom:10};

  const SelectCard=({selected,onClick,title,desc})=>(
    <div onClick={onClick} style={{
      padding:"14px 16px",borderRadius:10,cursor:"pointer",
      border:selected?`1px solid ${T.primary}`:"1px solid rgba(255,255,255,0.06)",
      background:selected?"rgba(0,212,170,0.07)":T.surface,
      transition:"all 0.15s",
    }}>
      <div style={{fontFamily:T.fontD,fontSize:12,fontWeight:700,letterSpacing:"0.06em",color:selected?T.primary:T.silver,marginBottom:4}}>{title}</div>
      <div style={{fontFamily:T.fontB,fontSize:11,color:T.dim,lineHeight:1.5}}>{desc}</div>
    </div>
  );

  return(
    <form onSubmit={handleSubmit} style={{maxWidth:680,margin:"0 auto",padding:"24px 28px 40px"}}>
      <div style={{marginBottom:28}}>
        <div style={{fontFamily:T.fontD,fontSize:9,fontWeight:700,letterSpacing:"0.14em",textTransform:"uppercase",color:T.primary,marginBottom:10}}>PLAN BUILDER</div>
        <h2 style={{fontFamily:T.fontD,fontSize:24,fontWeight:700,letterSpacing:"-0.01em",color:T.text,margin:0}}>GENERATE YOUR PLAN</h2>
      </div>

      <div style={{marginBottom:24}}>
        <label style={label}>GOAL</label>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
          {GOALS.map(g=><SelectCard key={g.value} selected={form.goal===g.value} onClick={()=>setForm(f=>({...f,goal:g.value}))} title={g.label} desc={g.desc}/>)}
        </div>
      </div>

      <div style={{marginBottom:24}}>
        <label style={label}>EXPERIENCE LEVEL</label>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:8}}>
          {LEVELS.map(l=><SelectCard key={l.value} selected={form.level===l.value} onClick={()=>setForm(f=>({...f,level:l.value}))} title={l.label} desc={l.desc}/>)}
        </div>
      </div>

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:20,marginBottom:24}}>
        <div>
          <label style={label}>DAYS PER WEEK: <span style={{color:T.primary}}>{form.days_per_week}</span></label>
          <input type="range" min={2} max={6} step={1} value={form.days_per_week} onChange={e=>setForm(f=>({...f,days_per_week:parseInt(e.target.value)}))} style={{width:"100%"}}/>
          <div style={{display:"flex",justifyContent:"space-between",fontFamily:T.fontD,fontSize:9,color:T.dim,marginTop:4}}><span>2</span><span>6</span></div>
        </div>
        <div>
          <label style={label}>PROGRAMME LENGTH: <span style={{color:T.primary}}>{form.weeks} WEEKS</span></label>
          <input type="range" min={4} max={16} step={4} value={form.weeks} onChange={e=>setForm(f=>({...f,weeks:parseInt(e.target.value)}))} style={{width:"100%"}}/>
          <div style={{display:"flex",justifyContent:"space-between",fontFamily:T.fontD,fontSize:9,color:T.dim,marginTop:4}}><span>4</span><span>16</span></div>
        </div>
      </div>

      <div style={{marginBottom:24}}>
        <label style={label}>INJURY HISTORY (select all that apply)</label>
        <div style={{display:"flex",flexWrap:"wrap",gap:8}}>
          {COMMON_INJURIES.map(inj=>{
            const sel=form.injuries.includes(inj);
            return(
              <button type="button" key={inj} onClick={()=>toggleInjury(inj)} style={{
                padding:"7px 16px",borderRadius:20,fontFamily:T.fontD,fontSize:10,fontWeight:700,letterSpacing:"0.08em",textTransform:"uppercase",cursor:"pointer",
                border:sel?`1px solid ${T.error}`:"1px solid rgba(255,255,255,0.08)",
                background:sel?"rgba(255,180,171,0.08)":"transparent",
                color:sel?T.error:T.dim,transition:"all 0.15s",
              }}>{inj.replace("_"," ")}</button>
            );
          })}
        </div>
      </div>

      <div style={{background:T.surface,borderRadius:12,padding:"18px 20px",marginBottom:24}}>
        <label style={label}>CURRENT 1RM MAXES (OPTIONAL)</label>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12}}>
          {Object.keys(form.current_maxes).map(k=>(
            <div key={k}>
              <label style={{fontFamily:T.fontD,fontSize:9,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",color:T.dim,display:"block",marginBottom:5}}>{k} (KG)</label>
              <input type="number" min={0} step={2.5} placeholder="e.g. 100" value={form.current_maxes[k]} onChange={e=>setForm(f=>({...f,current_maxes:{...f.current_maxes,[k]:e.target.value}}))} style={inp}/>
            </div>
          ))}
        </div>
      </div>

      {error&&<div style={{background:"rgba(255,180,171,0.08)",border:"1px solid rgba(255,180,171,0.2)",borderRadius:10,padding:"12px 16px",marginBottom:16,fontFamily:T.fontB,fontSize:13,color:T.error}}>⚠ {error}</div>}

      <button type="submit" disabled={loading} style={{
        width:"100%",padding:"14px",borderRadius:10,border:"none",cursor:loading?"not-allowed":"pointer",
        background:loading?T.card:`linear-gradient(135deg,${T.primary},${T.primaryD})`,
        color:loading?T.dim:"#131313",fontFamily:T.fontD,fontSize:13,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",
        display:"flex",alignItems:"center",justifyContent:"center",gap:10,
      }}>
        {loading&&<div style={{width:16,height:16,borderRadius:"50%",border:"2px solid #13131333",borderTopColor:"#131313",animation:"spin 0.8s linear infinite"}}/>}
        {loading?"GENERATING YOUR PLAN…":"GENERATE PLAN"}
      </button>
    </form>
  );
}
