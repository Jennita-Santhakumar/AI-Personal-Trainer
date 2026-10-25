import React, { useEffect, useState } from "react";
import api from "../../services/api";

const T = { bg:"#131313", surface:"#1c1b1b", card:"#201f1f", cardHigh:"#2a2a2a", primary:"#00d4aa", primaryD:"#00b896", silver:"#c8c6c6", dim:"#888580", text:"#e8e6df", error:"#ffb4ab", success:"#97c459", fontD:"'Space Grotesk',sans-serif", fontB:"'Lexend',sans-serif" };

const LEVEL_THRESHOLDS = [[0,"Beginner"],[500,"Novice"],[1500,"Intermediate"],[4000,"Advanced"],[10000,"Elite"]];
function getPrevThreshold(pts){ let prev=0; for(const[t] of LEVEL_THRESHOLDS){if(pts>=t)prev=t; else break;} return prev; }

const LEVEL_COLORS = { "Beginner":T.dim, "Novice":T.success, "Intermediate":"#85b7eb", "Advanced":"#c4b5fd", "Elite":T.primary };

function LevelBar({points,level,pointsToNext,levelThreshold}){
  const prev=getPrevThreshold(points);
  const span=levelThreshold-prev;
  const gained=points-prev;
  const pct=span>0?Math.min(100,Math.round((gained/span)*100)):100;
  const color=LEVEL_COLORS[level]||T.primary;
  return(
    <div style={{background:T.surface,borderRadius:14,padding:"22px 24px",marginBottom:16}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-end",marginBottom:12}}>
        <div>
          <div style={{fontFamily:T.fontD,fontSize:9,fontWeight:700,letterSpacing:"0.14em",textTransform:"uppercase",color:T.dim,marginBottom:6}}>CURRENT LEVEL</div>
          <div style={{fontFamily:T.fontD,fontSize:28,fontWeight:700,color,lineHeight:1}}>{level}</div>
          <div style={{fontFamily:T.fontB,fontSize:12,color:T.dim,marginTop:4}}>{points.toLocaleString()} pts</div>
        </div>
        <div style={{textAlign:"right"}}>
          {pointsToNext>0
            ?<div style={{fontFamily:T.fontB,fontSize:12,color:T.dim}}>{pointsToNext} pts to next level</div>
            :<div style={{fontFamily:T.fontD,fontSize:11,fontWeight:700,letterSpacing:"0.1em",color:T.primary}}>MAX LEVEL</div>}
        </div>
      </div>
      <div style={{height:5,background:T.cardHigh,borderRadius:3,overflow:"hidden"}}>
        <div style={{width:`${pct}%`,height:"100%",background:`linear-gradient(90deg,${color},${color}88)`,borderRadius:3,transition:"width 0.8s ease"}}/>
      </div>
    </div>
  );
}

function BadgeCard({badge}){
  const earned=badge.earned;
  return(
    <div title={badge.description} style={{
      display:"flex",flexDirection:"column",alignItems:"center",gap:8,
      padding:"18px 12px",borderRadius:12,textAlign:"center",
      background:earned?T.surface:T.card,
      border:earned?`1px solid rgba(0,212,170,0.15)`:"1px solid rgba(255,255,255,0.03)",
      opacity:earned?1:0.45,transition:"all 0.2s",
    }}>
      <div style={{width:52,height:52,borderRadius:"50%",background:earned?`linear-gradient(135deg,rgba(0,212,170,0.15),rgba(0,184,150,0.08))`:"rgba(255,255,255,0.03)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:24}}>
        {badge.icon}
      </div>
      <span style={{fontFamily:T.fontD,fontSize:11,fontWeight:700,letterSpacing:"0.05em",color:earned?T.silver:T.dim,lineHeight:1.3}}>{badge.name}</span>
      <span style={{fontFamily:T.fontB,fontSize:10,color:T.dim}}>
        {earned?(badge.earned_at||"Earned"):`${badge.points} pts`}
      </span>
    </div>
  );
}

export default function BadgeGrid(){
  const[status,setStatus]=useState(null);
  const[loading,setLoading]=useState(true);
  const[filter,setFilter]=useState("all");
  useEffect(()=>{ api.getGamificationStatus().then(setStatus).finally(()=>setLoading(false)); },[]);

  if(loading) return(
    <div style={{display:"flex",alignItems:"center",justifyContent:"center",padding:"4rem"}}>
      <div style={{width:28,height:28,borderRadius:"50%",border:`2px solid #00d4aa`,borderTopColor:"transparent",animation:"spin 0.8s linear infinite"}}/>
    </div>
  );
  if(!status)return null;

  const badges=status.badges||[];
  const filtered=filter==="earned"?badges.filter(b=>b.earned):filter==="locked"?badges.filter(b=>!b.earned):badges;
  const earnedCount=badges.filter(b=>b.earned).length;

  return(
    <div style={{padding:"0 28px 40px",maxWidth:760,margin:"0 auto"}}>
      <LevelBar points={status.points} level={status.level} pointsToNext={status.points_to_next_level} levelThreshold={status.level_threshold}/>

      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16}}>
        <div style={{fontFamily:T.fontD,fontSize:10,fontWeight:700,letterSpacing:"0.14em",textTransform:"uppercase",color:T.dim}}>
          {earnedCount}/{badges.length} BADGES EARNED
        </div>
        <div style={{display:"flex",gap:4,background:T.surface,borderRadius:8,padding:3}}>
          {["all","earned","locked"].map(f=>(
            <button key={f} onClick={()=>setFilter(f)} style={{padding:"5px 14px",borderRadius:6,border:"none",cursor:"pointer",fontFamily:T.fontD,fontSize:10,fontWeight:700,letterSpacing:"0.08em",textTransform:"uppercase",background:filter===f?`linear-gradient(135deg,${T.primary},${T.primaryD})`:"transparent",color:filter===f?"#131313":T.dim,transition:"all 0.15s"}}>{f}</button>
          ))}
        </div>
      </div>

      {status.streak>0&&(
        <div style={{background:`linear-gradient(135deg,rgba(0,212,170,0.08),rgba(0,184,150,0.04))`,border:`1px solid rgba(0,212,170,0.15)`,borderRadius:12,padding:"14px 18px",marginBottom:16,display:"flex",alignItems:"center",gap:14}}>
          <span style={{fontSize:24}}>🔥</span>
          <div>
            <div style={{fontFamily:T.fontD,fontSize:14,fontWeight:700,color:T.primary}}>{status.streak} DAY STREAK</div>
            <div style={{fontFamily:T.fontB,fontSize:11,color:T.dim,marginTop:2}}>Longest: {status.longest_streak} days · Keep going!</div>
          </div>
        </div>
      )}

      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))",gap:10}}>
        {filtered.map(b=><BadgeCard key={b.type} badge={b}/>)}
      </div>
    </div>
  );
}
