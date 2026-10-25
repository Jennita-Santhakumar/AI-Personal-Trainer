import React from "react";
import BadgeGrid from "../components/gamification/BadgeGrid";

const T = { fontD:"'Space Grotesk',sans-serif", primary:"#00d4aa", dim:"#888580", text:"#e8e6df" };

export default function BadgesPage(){
  return(
    <div>
      <div style={{ padding:"28px 28px 0" }}>
        <div style={{ fontFamily:T.fontD, fontSize:10, fontWeight:700, letterSpacing:"0.18em", textTransform:"uppercase", color:T.primary, marginBottom:10 }}>ACHIEVEMENTS</div>
        <h1 style={{ fontFamily:T.fontD, fontSize:"clamp(24px,4vw,42px)", fontWeight:700, letterSpacing:"-0.02em", color:T.text, margin:"0 0 24px" }}>PROGRESS & BADGES</h1>
      </div>
      <BadgeGrid />
    </div>
  );
}
