/**
 * PoseDetectionPage.jsx
 * Real-time form correction using MediaPipe Pose via TensorFlow.js.
 * Runs 100% in the browser — no backend needed for the CV part.
 * Sends form violation data to the backend when a session is logged.
 */
import React, { useRef, useEffect, useState, useCallback } from "react";

// ── Angle helpers ────────────────────────────────────────────────────────────

function angle3(a, b, c) {
  // Angle at point b formed by segments b→a and b→c
  const ab = [a.x - b.x, a.y - b.y];
  const cb = [c.x - b.x, c.y - b.y];
  const dot = ab[0]*cb[0] + ab[1]*cb[1];
  const magAB = Math.hypot(...ab);
  const magCB = Math.hypot(...cb);
  if (magAB === 0 || magCB === 0) return 0;
  return Math.acos(Math.max(-1, Math.min(1, dot / (magAB * magCB)))) * (180 / Math.PI);
}

// ── Form analyzers per exercise ───────────────────────────────────────────────

const ANALYZERS = {
  squat(lm) {
    const issues = [];
    // LEFT side
    const lHip  = lm[23], lKnee = lm[25], lAnk = lm[27], lShoulder = lm[11];
    const rHip  = lm[24], rKnee = lm[26], rAnk = lm[28], rShoulder = lm[12];

    const kneeAngleL = angle3(lHip, lKnee, lAnk);
    const kneeAngleR = angle3(rHip, rKnee, rAnk);

    // Knee cave: knee x should be between hip x and ankle x
    if (lKnee.x < lHip.x - 0.04) issues.push({ text:"Left knee caving in — push knee out over toes", severity:"danger" });
    if (rKnee.x > rHip.x + 0.04) issues.push({ text:"Right knee caving in — push knee out over toes", severity:"danger" });

    // Forward lean: shoulder x vs hip x
    const torsoLean = Math.abs(lShoulder.x - lHip.x);
    if (torsoLean > 0.12) issues.push({ text:"Excessive forward lean — chest up, proud chest", severity:"warning" });

    // Depth check
    if (kneeAngleL > 110 && lm[23].visibility > 0.7) issues.push({ text:"Depth short — go below parallel", severity:"info" });

    if (issues.length === 0) issues.push({ text:"✓ Good squat form — keep it up!", severity:"good" });
    return issues;
  },

  deadlift(lm) {
    const issues = [];
    const lShoulder = lm[11], rShoulder = lm[12];
    const lHip = lm[23], rHip = lm[24];
    const lKnee = lm[25], rKnee = lm[26];

    // Rounded back: shoulders should be above hips during pull
    const shoulderMidY = (lShoulder.y + rShoulder.y) / 2;
    const hipMidY = (lHip.y + rHip.y) / 2;
    const kneeMidY = (lKnee.y + rKnee.y) / 2;

    // If hips are higher than shoulders (squat-to-deadlift / stripper pull)
    if (hipMidY < shoulderMidY - 0.05 && lm[23].visibility > 0.6) {
      issues.push({ text:"Hips shooting up — keep hips and shoulders rising together", severity:"danger" });
    }

    // Shoulder position: should be over or slightly behind bar (forward of hips at setup)
    if (lShoulder.x - lHip.x > 0.15) {
      issues.push({ text:"Bar drifting — keep bar close to legs throughout", severity:"warning" });
    }

    if (issues.length === 0) issues.push({ text:"✓ Good deadlift positioning!", severity:"good" });
    return issues;
  },

  pushup(lm) {
    const issues = [];
    const lShoulder = lm[11], lHip = lm[23], lAnkle = lm[27];
    const rShoulder = lm[12], rHip = lm[24];

    // Body line: hip should be between shoulder and ankle
    const shoulderY = (lShoulder.y + rShoulder.y) / 2;
    const hipY = (lHip.y + rHip.y) / 2;

    if (hipY - shoulderY > 0.08) issues.push({ text:"Hips sagging — squeeze glutes and brace core", severity:"danger" });
    if (shoulderY - hipY > 0.08) issues.push({ text:"Hips piked too high — lower them into a straight line", severity:"warning" });

    // Elbow flare (using wrist-elbow-shoulder angle)
    const lElbow = lm[13], lWrist = lm[15];
    if (lElbow.visibility > 0.7) {
      const elbowAngle = angle3(lShoulder, lElbow, lWrist);
      if (elbowAngle < 60) issues.push({ text:"Elbows too wide — bring to 45° from body", severity:"warning" });
    }

    if (issues.length === 0) issues.push({ text:"✓ Great push-up form!", severity:"good" });
    return issues;
  },

  lunge(lm) {
    const issues = [];
    const lHip = lm[23], lKnee = lm[25], lAnk = lm[27];
    const rKnee = lm[26];

    // Front knee should stay over ankle
    if (lKnee.x - lAnk.x > 0.1) issues.push({ text:"Front knee too far forward — step wider", severity:"warning" });

    // Knee cave
    if (lKnee.x < lHip.x - 0.05) issues.push({ text:"Front knee caving in — push out over pinky toe", severity:"danger" });

    if (issues.length === 0) issues.push({ text:"✓ Solid lunge technique!", severity:"good" });
    return issues;
  },

  plank(lm) {
    const issues = [];
    const lShoulder = lm[11], rShoulder = lm[12];
    const lHip = lm[23], rHip = lm[24];
    const lAnkle = lm[27];

    const shoulderY = (lShoulder.y + rShoulder.y) / 2;
    const hipY = (lHip.y + rHip.y) / 2;

    if (hipY - shoulderY > 0.07) issues.push({ text:"Hips dropping — squeeze glutes hard", severity:"danger" });
    if (shoulderY - hipY > 0.07) issues.push({ text:"Hips too high — lower to straight line", severity:"warning" });

    if (issues.length === 0) issues.push({ text:"✓ Solid plank position!", severity:"good" });
    return issues;
  },
};

// ── Drawing helpers ───────────────────────────────────────────────────────────

const POSE_CONNECTIONS = [
  [11,12],[11,13],[13,15],[12,14],[14,16],
  [11,23],[12,24],[23,24],
  [23,25],[25,27],[24,26],[26,28],
  [27,29],[28,30],[29,31],[30,32],
];

function drawPose(ctx, lm, w, h, issues) {
  const hasIssue = issues.some(i => i.severity === "danger");
  const skelColor = hasIssue ? "#ef4444" : "#22c55e";

  ctx.clearRect(0, 0, w, h);

  // Connections
  ctx.lineWidth = 2.5;
  ctx.strokeStyle = skelColor + "aa";
  POSE_CONNECTIONS.forEach(([a, b]) => {
    if (!lm[a] || !lm[b]) return;
    if (lm[a].visibility < 0.4 || lm[b].visibility < 0.4) return;
    ctx.beginPath();
    ctx.moveTo(lm[a].x * w, lm[a].y * h);
    ctx.lineTo(lm[b].x * w, lm[b].y * h);
    ctx.stroke();
  });

  // Keypoints
  lm.forEach((kp) => {
    if (kp.visibility < 0.4) return;
    ctx.beginPath();
    ctx.arc(kp.x * w, kp.y * h, 5, 0, 2 * Math.PI);
    ctx.fillStyle = skelColor;
    ctx.fill();
  });
}

// ── Issue badge ───────────────────────────────────────────────────────────────

function IssueBadge({ issue }) {
  const colors = {
    danger:  ["#fee2e2","#991b1b"],
    warning: ["#fef3c7","#92400e"],
    info:    ["#dbeafe","#1e40af"],
    good:    ["#dcfce7","#166534"],
  };
  const [bg, fg] = colors[issue.severity] || colors.info;
  return (
    <div style={{ padding:"8px 14px", borderRadius:10, background:bg,
      color:fg, fontSize:13, fontWeight:500, lineHeight:1.5 }}>
      {issue.text}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

const EXERCISES = [
  { key:"squat",    label:"Squat"     },
  { key:"deadlift", label:"Deadlift"  },
  { key:"pushup",   label:"Push-up"   },
  { key:"lunge",    label:"Lunge"     },
  { key:"plank",    label:"Plank"     },
];

export default function PoseDetectionPage() {
  const videoRef   = useRef(null);
  const canvasRef  = useRef(null);
  const poseRef    = useRef(null);
  const rafRef     = useRef(null);
  const [exercise,   setExercise]   = useState("squat");
  const [issues,     setIssues]     = useState([]);
  const [status,     setStatus]     = useState("idle"); // idle | loading | running | error
  const [errorMsg,   setErrorMsg]   = useState("");
  const [repCount,   setRepCount]   = useState(0);
  const [repState,   setRepState]   = useState("up"); // up | down
  const repStateRef = useRef("up");

  const analyze = useCallback((results) => {
    if (!results.poseLandmarks) return;
    const lm = results.poseLandmarks;
    const analyzer = ANALYZERS[exercise];
    const found = analyzer ? analyzer(lm) : [];
    setIssues(found);

    // Simple rep counter using knee angle for squat
    if (exercise === "squat" && lm[25] && lm[23] && lm[27]) {
      const ka = angle3(lm[23], lm[25], lm[27]);
      if (ka < 100 && repStateRef.current === "up") {
        repStateRef.current = "down";
        setRepState("down");
      } else if (ka > 155 && repStateRef.current === "down") {
        repStateRef.current = "up";
        setRepState("up");
        setRepCount(c => c + 1);
      }
    }
    if (exercise === "pushup" && lm[13] && lm[11] && lm[15]) {
      const ea = angle3(lm[11], lm[13], lm[15]);
      if (ea < 90 && repStateRef.current === "up") {
        repStateRef.current = "down"; setRepState("down");
      } else if (ea > 155 && repStateRef.current === "down") {
        repStateRef.current = "up"; setRepState("up");
        setRepCount(c => c + 1);
      }
    }

    // Draw skeleton
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    drawPose(ctx, lm, canvas.width, canvas.height, found);
  }, [exercise]);

  const startCamera = useCallback(async () => {
    setStatus("loading"); setErrorMsg("");
    try {
      // Load MediaPipe via CDN
      if (!window.Pose) {
        await new Promise((res, rej) => {
          const s1 = document.createElement("script");
          s1.src = "https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js";
          s1.onload = res; s1.onerror = rej;
          document.head.appendChild(s1);
        });
        await new Promise((res, rej) => {
          const s2 = document.createElement("script");
          s2.src = "https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js";
          s2.onload = res; s2.onerror = rej;
          document.head.appendChild(s2);
        });
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" }
      });
      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      // eslint-disable-next-line no-undef
      const pose = new Pose({
        locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${f}`
      });
      pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        enableSegmentation: false,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });
      pose.onResults(analyze);
      poseRef.current = pose;

      const runFrame = async () => {
        if (videoRef.current && videoRef.current.readyState === 4) {
          await pose.send({ image: videoRef.current });
        }
        rafRef.current = requestAnimationFrame(runFrame);
      };
      rafRef.current = requestAnimationFrame(runFrame);
      setStatus("running");
    } catch (e) {
      setErrorMsg(e.message || "Camera access failed");
      setStatus("error");
    }
  }, [analyze]);

  const stop = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(t => t.stop());
      videoRef.current.srcObject = null;
    }
    poseRef.current = null;
    setStatus("idle"); setIssues([]);
  }, []);

  // Re-run analyze when exercise changes (updates the closure)
  useEffect(() => {
    if (poseRef.current) poseRef.current.onResults(analyze);
  }, [analyze]);

  useEffect(() => () => stop(), [stop]);

  const s = (base, extra={}) => ({ ...base, ...extra });

  return (
    <div style={{ padding:"1.5rem", maxWidth:860, margin:"0 auto" }}>
      <h2 style={{ fontSize:20, fontWeight:600, marginBottom:4 }}>📷 Real-Time Form Check</h2>
      <p style={{ fontSize:13, color:"var(--color-text-secondary)", marginBottom:20 }}>
        AI watches your movement via webcam and flags form issues instantly — powered by MediaPipe Pose.
      </p>

      {/* Exercise selector */}
      <div style={{ display:"flex", gap:8, marginBottom:16, flexWrap:"wrap" }}>
        {EXERCISES.map(e => (
          <button key={e.key} onClick={() => { setExercise(e.key); setRepCount(0); repStateRef.current = "up"; }}
            style={{ padding:"7px 16px", borderRadius:20, fontSize:13, cursor:"pointer", fontWeight:500,
              border: exercise===e.key ? "2px solid #534AB7" : "0.5px solid var(--color-border-secondary)",
              background: exercise===e.key ? "var(--color-background-info)" : "transparent",
              color: exercise===e.key ? "var(--color-text-info)" : "var(--color-text-secondary)" }}>
            {e.label}
          </button>
        ))}
      </div>

      {/* Camera view */}
      <div style={{ position:"relative", background:"#000", borderRadius:14,
        overflow:"hidden", aspectRatio:"4/3", marginBottom:16,
        border:"0.5px solid var(--color-border-tertiary)" }}>
        <video ref={videoRef} muted playsInline
          style={{ width:"100%", height:"100%", objectFit:"cover", transform:"scaleX(-1)", display: status==="running" ? "block" : "none" }} />
        <canvas ref={canvasRef} width={640} height={480}
          style={{ position:"absolute", top:0, left:0, width:"100%", height:"100%",
            transform:"scaleX(-1)", display: status==="running" ? "block" : "none" }} />

        {status !== "running" && (
          <div style={{ position:"absolute", inset:0, display:"flex", flexDirection:"column",
            alignItems:"center", justifyContent:"center", gap:12, color:"#fff" }}>
            {status === "idle" && (
              <>
                <div style={{ fontSize:48 }}>📷</div>
                <div style={{ fontSize:14, color:"#aaa" }}>Camera off</div>
                <button onClick={startCamera}
                  style={{ padding:"10px 28px", borderRadius:10, border:"none",
                    background:"#534AB7", color:"#fff", fontSize:15, fontWeight:600, cursor:"pointer" }}>
                  Start Form Check
                </button>
              </>
            )}
            {status === "loading" && (
              <>
                <div style={{ width:36, height:36, borderRadius:"50%",
                  border:"3px solid #534AB7", borderTopColor:"transparent",
                  animation:"spin 0.8s linear infinite" }} />
                <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
                <div style={{ fontSize:13, color:"#aaa" }}>Loading AI model…</div>
              </>
            )}
            {status === "error" && (
              <>
                <div style={{ fontSize:32 }}>⚠️</div>
                <div style={{ fontSize:13, color:"#fca5a5", textAlign:"center", maxWidth:300 }}>{errorMsg}</div>
                <div style={{ fontSize:12, color:"#888", textAlign:"center", maxWidth:280 }}>
                  Make sure your browser has camera permission and you're on HTTPS or localhost.
                </div>
                <button onClick={startCamera}
                  style={{ padding:"8px 20px", borderRadius:8, border:"none",
                    background:"#534AB7", color:"#fff", fontSize:13, cursor:"pointer" }}>
                  Retry
                </button>
              </>
            )}
          </div>
        )}

        {/* Rep counter overlay */}
        {status === "running" && (
          <div style={{ position:"absolute", top:12, right:12,
            background:"rgba(0,0,0,0.7)", borderRadius:10,
            padding:"8px 14px", color:"#fff", textAlign:"center" }}>
            <div style={{ fontSize:28, fontWeight:700, lineHeight:1 }}>{repCount}</div>
            <div style={{ fontSize:10, color:"#aaa", marginTop:2 }}>REPS</div>
          </div>
        )}

        {/* Phase indicator */}
        {status === "running" && (exercise === "squat" || exercise === "pushup") && (
          <div style={{ position:"absolute", top:12, left:12,
            background: repState==="down" ? "rgba(83,74,183,0.8)" : "rgba(34,197,94,0.8)",
            borderRadius:8, padding:"5px 12px", color:"#fff", fontSize:12, fontWeight:600 }}>
            {repState === "down" ? "DOWN ↓" : "UP ↑"}
          </div>
        )}
      </div>

      {/* Controls */}
      <div style={{ display:"flex", gap:8, marginBottom:16 }}>
        {status === "running" ? (
          <button onClick={stop}
            style={{ padding:"9px 22px", borderRadius:9, border:"none",
              background:"var(--color-background-danger)", color:"var(--color-text-danger)",
              fontSize:14, fontWeight:500, cursor:"pointer" }}>
            ⏹ Stop Camera
          </button>
        ) : (
          <button onClick={startCamera} disabled={status==="loading"}
            style={{ padding:"9px 22px", borderRadius:9, border:"none",
              background:"#534AB7", color:"#fff", fontSize:14, fontWeight:500,
              cursor: status==="loading" ? "not-allowed" : "pointer",
              opacity: status==="loading" ? 0.6 : 1 }}>
            ▶ Start Camera
          </button>
        )}
        {status === "running" && (
          <button onClick={() => { setRepCount(0); repStateRef.current = "up"; }}
            style={{ padding:"9px 16px", borderRadius:9, fontSize:13,
              border:"0.5px solid var(--color-border-secondary)",
              background:"transparent", color:"var(--color-text-secondary)", cursor:"pointer" }}>
            Reset reps
          </button>
        )}
      </div>

      {/* Live feedback */}
      {issues.length > 0 && (
        <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
          <div style={{ fontSize:12, fontWeight:600, textTransform:"uppercase",
            letterSpacing:"0.05em", color:"var(--color-text-tertiary)", marginBottom:4 }}>
            Live Feedback
          </div>
          {issues.map((issue, i) => <IssueBadge key={i} issue={issue} />)}
        </div>
      )}

      {/* Static tips when camera off */}
      {status !== "running" && (
        <div style={{ background:"var(--color-background-secondary)", borderRadius:12,
          padding:"14px 16px", marginTop:8 }}>
          <div style={{ fontSize:12, fontWeight:600, color:"var(--color-text-tertiary)",
            textTransform:"uppercase", letterSpacing:"0.05em", marginBottom:10 }}>
            Setup tips
          </div>
          <ul style={{ fontSize:13, color:"var(--color-text-secondary)", lineHeight:2,
            paddingLeft:16, margin:0 }}>
            <li>Stand 1.5–2m from camera so full body is visible</li>
            <li>Face the camera sideways for squat/deadlift, forward for push-up</li>
            <li>Good lighting — your body needs to be clearly visible</li>
            <li>Wear fitted clothes so joint positions are clear</li>
            <li>Works on Chrome, Edge, Firefox (desktop)</li>
          </ul>
        </div>
      )}
    </div>
  );
}
