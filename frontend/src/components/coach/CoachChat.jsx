/**
 * CoachChat.jsx — The All Fit Design System
 */
import React, { useState, useRef, useEffect } from "react";
import { useCoach } from "../../hooks/useCoach";

const T = {
  bg:"#131313", surface:"#1c1b1b", card:"#201f1f", cardHigh:"#2a2a2a",
  primary:"#00d4aa", primaryD:"#00b896", silver:"#c8c6c6", dim:"#888580",
  text:"#e8e6df", error:"#ffb4ab",
  fontD:"'Space Grotesk',sans-serif", fontB:"'Lexend',sans-serif",
};

const QUICK_PROMPTS = [
  "How did I do in my last session?",
  "What should I focus on today?",
  "How do I fix my knee cave on squats?",
  "Am I ready to add weight to my squat?",
  "What are my biggest injury risks right now?",
  "Give me a mobility routine for powerlifters",
];

function formatTs(ts){ if(!ts)return""; return new Date(ts).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}); }

function TypingDots(){
  return(
    <span style={{display:"inline-flex",alignItems:"center",gap:4}}>
      {[0,1,2].map(i=>(
        <span key={i} style={{width:5,height:5,borderRadius:"50%",background:T.primary,display:"inline-block",animation:"bounce 1.2s ease-in-out infinite",animationDelay:`${i*0.2}s`}}/>
      ))}
    </span>
  );
}

const MAX_CHARS = 600;

export default function CoachChat({ currentSessionId = null }){
  const{messages,streaming,error,sendMessage,clearHistory}=useCoach();
  const[input,setInput]=useState("");
  const bottomRef=useRef(null);
  const ollamaStarting=error&&(error.toLowerCase().includes("starting up")||error.toLowerCase().includes("model")||error.toLowerCase().includes("connect")||error.toLowerCase().includes("502")||error.toLowerCase().includes("503"));

  useEffect(()=>{ bottomRef.current?.scrollIntoView({behavior:"smooth"}); },[messages]);

  const handleSend=(text)=>{
    const msg=(text||input).trim();
    if(!msg||msg.length>MAX_CHARS||streaming)return;
    sendMessage(msg,currentSessionId); setInput("");
  };

  return(
    <div style={{display:"flex",flexDirection:"column",height:"100%",minHeight:500,background:T.bg}}>

      {/* Header */}
      <div style={{padding:"20px 28px",borderBottom:`1px solid rgba(255,255,255,0.04)`,display:"flex",alignItems:"center",justifyContent:"space-between",flexShrink:0}}>
        <div>
          <div style={{fontFamily:T.fontD,fontSize:10,fontWeight:700,letterSpacing:"0.18em",textTransform:"uppercase",color:T.primary,marginBottom:4}}>AI POWERED</div>
          <div style={{fontFamily:T.fontD,fontSize:20,fontWeight:700,letterSpacing:"-0.01em",color:T.text}}>ALL FIT COACH</div>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div style={{width:10,height:10,borderRadius:"50%",background:T.primary,animation:"kl-pulse 2s ease-in-out infinite"}}/>
          {messages.length>0&&(
            <button onClick={clearHistory} style={{fontFamily:T.fontD,fontSize:10,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",padding:"6px 14px",borderRadius:8,border:`1px solid rgba(255,255,255,0.08)`,background:"transparent",color:T.dim,cursor:"pointer"}}>CLEAR</button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div style={{flex:1,overflowY:"auto",padding:"24px 28px",display:"flex",flexDirection:"column",gap:16}}>

        {messages.length===0&&!error&&(
          <div style={{textAlign:"center",paddingTop:48}}>
            <div style={{width:64,height:64,borderRadius:"50%",background:`linear-gradient(135deg,${T.primary},${T.primaryD})`,display:"flex",alignItems:"center",justifyContent:"center",margin:"0 auto 20px",fontSize:28,animation:"kl-pulse 2s ease-in-out infinite"}}>🤖</div>
            <div style={{fontFamily:T.fontD,fontSize:14,fontWeight:600,letterSpacing:"0.05em",color:T.silver,marginBottom:6}}>YOUR AI COACH IS READY</div>
            <div style={{fontFamily:T.fontB,fontSize:13,color:T.dim,marginBottom:28}}>Powered by llama3.1:8b — fully local, no cloud.</div>
            <div style={{display:"flex",flexWrap:"wrap",gap:8,justifyContent:"center",maxWidth:600,margin:"0 auto"}}>
              {QUICK_PROMPTS.map(p=>(
                <button key={p} onClick={()=>handleSend(p)} style={{fontFamily:T.fontB,fontSize:12,padding:"8px 16px",borderRadius:20,border:`1px solid rgba(255,255,255,0.08)`,background:T.surface,color:T.silver,cursor:"pointer",transition:"all 0.15s"}}
                  onMouseEnter={e=>{e.target.style.borderColor=T.primary;e.target.style.color=T.primary;}}
                  onMouseLeave={e=>{e.target.style.borderColor="rgba(255,255,255,0.08)";e.target.style.color=T.silver;}}>
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {ollamaStarting&&(
          <div style={{margin:"2rem auto",maxWidth:500,background:"rgba(65,36,2,0.5)",border:`1px solid rgba(0,212,170,0.2)`,borderRadius:14,padding:"22px 24px",textAlign:"center"}}>
            <div style={{fontSize:28,marginBottom:10}}>⏳</div>
            <div style={{fontFamily:T.fontD,fontSize:13,fontWeight:700,letterSpacing:"0.08em",color:T.primary,marginBottom:8}}>AI MODEL LOADING</div>
            <div style={{fontFamily:T.fontB,fontSize:13,color:T.silver,lineHeight:1.7}}>Ollama is starting up or downloading <strong>llama3.1:8b</strong>. This only happens once.</div>
          </div>
        )}

        {!ollamaStarting&&error&&(
          <div style={{background:"rgba(80,19,19,0.5)",border:`1px solid rgba(255,180,171,0.2)`,borderRadius:12,padding:"14px 18px",fontFamily:T.fontB,fontSize:13,color:T.error}}>⚠ {error}</div>
        )}

        {messages.map((msg,idx)=>{
          const isUser=msg.role==="user";
          return(
            <div key={idx} style={{display:"flex",justifyContent:isUser?"flex-end":"flex-start",animation:"fadeUp 0.3s ease"}}>
              {!isUser&&(
                <div style={{width:32,height:32,borderRadius:"50%",background:`linear-gradient(135deg,${T.primary},${T.primaryD})`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:14,flexShrink:0,marginRight:10,marginTop:2}}>🤖</div>
              )}
              <div style={{maxWidth:"72%"}}>
                <div style={{
                  padding:"12px 16px",borderRadius:isUser?"14px 14px 4px 14px":"14px 14px 14px 4px",
                  background:isUser?`linear-gradient(135deg,${T.primary},${T.primaryD})`:T.surface,
                  color:isUser?"#131313":T.silver,
                  fontFamily:T.fontB,fontSize:14,lineHeight:1.7,
                  whiteSpace:"pre-wrap",wordBreak:"break-word",
                }}>
                  {msg.content||<TypingDots/>}
                </div>
                {msg.timestamp&&<div style={{fontFamily:T.fontD,fontSize:9,color:T.dim,marginTop:4,textAlign:isUser?"right":"left",letterSpacing:"0.05em"}}>{formatTs(msg.timestamp)}</div>}
              </div>
            </div>
          );
        })}
        {streaming&&messages[messages.length-1]?.role==="user"&&(
          <div style={{display:"flex",alignItems:"flex-start",gap:10}}>
            <div style={{width:32,height:32,borderRadius:"50%",background:`linear-gradient(135deg,${T.primary},${T.primaryD})`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:14,flexShrink:0}}>🤖</div>
            <div style={{background:T.surface,borderRadius:"14px 14px 14px 4px",padding:"14px 18px"}}><TypingDots/></div>
          </div>
        )}
        <div ref={bottomRef}/>
      </div>

      {/* Input */}
      <div style={{padding:"16px 28px",borderTop:`1px solid rgba(255,255,255,0.04)`,flexShrink:0}}>
        <div style={{display:"flex",gap:10,alignItems:"flex-end"}}>
          <div style={{flex:1,position:"relative"}}>
            <textarea
              value={input} onChange={e=>setInput(e.target.value)}
              onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();handleSend();}}}
              placeholder="Ask your coach anything…"
              rows={1}
              style={{
                width:"100%",padding:"12px 16px",borderRadius:12,
                border:`1px solid rgba(255,255,255,0.08)`,
                background:T.surface,color:T.text,fontFamily:T.fontB,fontSize:14,
                outline:"none",resize:"none",boxSizing:"border-box",lineHeight:1.5,
                maxHeight:120,overflowY:"auto",
              }}
            />
            {input.length>MAX_CHARS*0.8&&(
              <div style={{position:"absolute",right:10,bottom:8,fontFamily:T.fontD,fontSize:9,color:input.length>MAX_CHARS?T.error:T.dim}}>
                {input.length}/{MAX_CHARS}
              </div>
            )}
          </div>
          <button onClick={()=>handleSend()} disabled={!input.trim()||streaming||input.length>MAX_CHARS}
            style={{
              padding:"12px 20px",borderRadius:12,border:"none",cursor:"pointer",flexShrink:0,
              background:!input.trim()||streaming?T.card:`linear-gradient(135deg,${T.primary},${T.primaryD})`,
              color:!input.trim()||streaming?T.dim:"#131313",
              fontFamily:T.fontD,fontSize:12,fontWeight:700,letterSpacing:"0.08em",textTransform:"uppercase",
              transition:"all 0.2s",
            }}>
            {streaming?"…":"SEND"}
          </button>
        </div>
      </div>
    </div>
  );
}
