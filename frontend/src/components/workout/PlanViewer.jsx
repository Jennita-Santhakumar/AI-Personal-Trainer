import React, { useState } from "react";

const T = { bg:"#131313", surface:"#1c1b1b", card:"#201f1f", cardHigh:"#2a2a2a", primary:"#00d4aa", primaryD:"#00b896", silver:"#c8c6c6", dim:"#888580", text:"#e8e6df", fontD:"'Space Grotesk',sans-serif", fontB:"'Lexend',sans-serif" };

const FOCUS_COLORS = {
  strength:["rgba(0,212,170,0.12)",T.primary], hypertrophy:["rgba(151,196,89,0.12)","#97c459"],
  endurance:["rgba(133,183,235,0.12)","#85b7eb"], speed:["rgba(0,212,170,0.12)",T.primary],
  cardio:["rgba(0,212,170,0.12)",T.primary], flexibility:["rgba(255,180,171,0.12)","#ffb4ab"],
  recovery:["rgba(151,196,89,0.12)","#97c459"], general:["rgba(200,198,198,0.08)",T.silver],
};

function ExerciseRow({exercise}){
  const[expanded,setExpanded]=useState(false);
  return(
    <div>
      <div onClick={()=>exercise.notes&&setExpanded(e=>!e)} style={{
        display:"grid",gridTemplateColumns:"1fr 70px 100px 60px",gap:"0 12px",padding:"10px 0",
        alignItems:"center",borderBottom:"1px solid rgba(255,255,255,0.03)",
        cursor:exercise.notes?"pointer":"default",
      }}>
        <span style={{fontFamily:T.fontB,fontSize:13,color:T.silver}}>
          {exercise.name}
          {exercise.notes&&<span style={{fontSize:10,color:T.dim,marginLeft:6}}>▾</span>}
        </span>
        <span style={{fontFamily:T.fontD,fontSize:13,fontWeight:600,color:T.text,textAlign:"center"}}>{exercise.sets}×{exercise.reps}</span>
        <span style={{fontFamily:T.fontB,fontSize:11,color:"#85b7eb"}}>{exercise.intensity}</span>
        <span style={{fontFamily:T.fontB,fontSize:11,color:T.dim}}>{exercise.rest_seconds>0?`${exercise.rest_seconds}s`:"—"}</span>
      </div>
      {expanded&&exercise.notes&&(
        <div style={{fontFamily:T.fontB,fontSize:12,color:T.dim,padding:"6px 0 10px",fontStyle:"italic",lineHeight:1.6}}>{exercise.notes}</div>
      )}
    </div>
  );
}

function DayCard({day}){
  const[open,setOpen]=useState(false);
  const focus=day.focus||"general";
  const[bg,fg]=FOCUS_COLORS[focus]||FOCUS_COLORS.general;
  return(
    <div style={{background:T.surface,borderRadius:12,marginBottom:8,overflow:"hidden"}}>
      <div onClick={()=>setOpen(o=>!o)} style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"14px 18px",cursor:"pointer"}}>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div>
            <div style={{fontFamily:T.fontD,fontSize:13,fontWeight:700,color:T.text}}>{day.day_name}</div>
            <div style={{fontFamily:T.fontB,fontSize:11,color:T.dim,marginTop:2}}>{day.session_name}</div>
          </div>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <span style={{fontFamily:T.fontD,fontSize:10,fontWeight:700,letterSpacing:"0.08em",textTransform:"uppercase",padding:"4px 10px",borderRadius:6,background:bg,color:fg}}>{focus}</span>
          <span style={{fontFamily:T.fontB,fontSize:11,color:T.dim}}>{day.duration_minutes} min</span>
          <span style={{color:T.dim,fontSize:12}}>{open?"▲":"▼"}</span>
        </div>
      </div>
      {open&&(
        <div style={{padding:"0 18px 16px",borderTop:"1px solid rgba(255,255,255,0.04)"}}>
          {day.warmup?.length>0&&(
            <div style={{marginTop:12,marginBottom:12}}>
              <div style={{fontFamily:T.fontD,fontSize:9,fontWeight:700,letterSpacing:"0.12em",textTransform:"uppercase",color:T.dim,marginBottom:6}}>WARMUP</div>
              <div style={{fontFamily:T.fontB,fontSize:12,color:T.silver}}>{day.warmup.join(" · ")}</div>
            </div>
          )}
          <div style={{marginTop:12}}>
            <div style={{display:"grid",gridTemplateColumns:"1fr 70px 100px 60px",gap:"0 12px",padding:"0 0 6px",marginBottom:4,borderBottom:"1px solid rgba(255,255,255,0.06)"}}>
              {["EXERCISE","SETS×REPS","INTENSITY","REST"].map(h=>(
                <span key={h} style={{fontFamily:T.fontD,fontSize:8,fontWeight:700,letterSpacing:"0.12em",textTransform:"uppercase",color:T.dim}}>{h}</span>
              ))}
            </div>
            {(day.exercises||[]).map((ex,i)=><ExerciseRow key={i} exercise={ex}/>)}
          </div>
          {day.cooldown?.length>0&&(
            <div style={{marginTop:12}}>
              <div style={{fontFamily:T.fontD,fontSize:9,fontWeight:700,letterSpacing:"0.12em",textTransform:"uppercase",color:T.dim,marginBottom:6}}>COOLDOWN</div>
              <div style={{fontFamily:T.fontB,fontSize:12,color:T.silver}}>{day.cooldown.join(" · ")}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function PlanViewer({plan}){
  const[selectedWeek,setSelectedWeek]=useState(0);
  if(!plan?.plan?.length)return null;
  const weeks=plan.plan;
  const week=weeks[selectedWeek];
  return(
    <div style={{maxWidth:760,margin:"0 auto",padding:"24px 28px 40px"}}>
      <div style={{marginBottom:24}}>
        <div style={{fontFamily:T.fontD,fontSize:11,fontWeight:700,letterSpacing:"0.12em",textTransform:"uppercase",color:T.silver,marginBottom:4}}>{plan.goal} PLAN · {plan.level}</div>
        <div style={{fontFamily:T.fontB,fontSize:12,color:T.dim}}>{plan.weeks} weeks · Click any day to expand exercises</div>
      </div>

      <div style={{display:"flex",gap:6,marginBottom:20,flexWrap:"wrap"}}>
        {weeks.map((w,i)=>(
          <button key={i} onClick={()=>setSelectedWeek(i)} style={{
            padding:"7px 16px",borderRadius:20,fontSize:11,cursor:"pointer",fontFamily:T.fontD,fontWeight:700,letterSpacing:"0.08em",
            border:selectedWeek===i?`1px solid ${T.primary}`:"1px solid rgba(255,255,255,0.08)",
            background:selectedWeek===i?"rgba(0,212,170,0.08)":"transparent",
            color:selectedWeek===i?T.primary:T.dim,transition:"all 0.15s",
          }}>WEEK {w.week_number}{w.deload?" (DELOAD)":""}</button>
        ))}
      </div>

      {week.overload_note&&(
        <div style={{background:T.surface,borderRadius:10,padding:"12px 16px",marginBottom:16,borderLeft:`2px solid ${T.primary}`,fontFamily:T.fontB,fontSize:13,color:T.dim,fontStyle:"italic"}}>{week.overload_note}</div>
      )}

      {(week.days||[]).map((day,i)=><DayCard key={i} day={day}/>)}
    </div>
  );
}
