/**
 * Dashboard.jsx — Full-Stack Fitness Roadmap Hub & Dashboard
 * Integrates multi-week LLM-generated Workout & Nutrition Roadmaps with
 * Form AI, Nutrition Tracker, and AI Coach quick shortcuts.
 */
import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";
import RoadmapGeneratorForm from "../roadmap/RoadmapGeneratorForm";
import RoadmapViewer from "../roadmap/RoadmapViewer";

const T = {
  bg: "#131313",
  surface: "#1c1b1b",
  card: "#201f1f",
  cardHigh: "#2a2a2a",
  primary: "#00d4aa",
  primaryD: "#00b896",
  silver: "#c8c6c6",
  dim: "#888580",
  text: "#e8e6df",
  error: "#ffb4ab",
  success: "#97c459",
  info: "#85b7eb",
  fontD: "'Space Grotesk', sans-serif",
  fontB: "'Lexend', sans-serif",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [activeRoadmap, setActiveRoadmap] = useState(null);
  const [roadmapHistory, setRoadmapHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showGenerator, setShowGenerator] = useState(false);
  const [stats, setStats] = useState({ sessions: 0, streak: 0, points: 0, quality: "0.0" });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [roadmapRes, historyRes, gamificationRes, sessionsRes] = await Promise.allSettled([
        api.getCurrentRoadmap(),
        api.getRoadmapHistory(),
        api.getGamificationStatus(),
        api.getSessionHistory(10),
      ]);

      if (roadmapRes.status === "fulfilled" && roadmapRes.value) {
        setActiveRoadmap(roadmapRes.value);
        setShowGenerator(false);
      } else {
        setActiveRoadmap(null);
        setShowGenerator(true);
      }

      if (historyRes.status === "fulfilled" && Array.isArray(historyRes.value)) {
        setRoadmapHistory(historyRes.value);
      }

      const gam = gamificationRes.status === "fulfilled" ? gamificationRes.value : {};
      const sess = sessionsRes.status === "fulfilled" && Array.isArray(sessionsRes.value) ? sessionsRes.value : [];
      
      const avgQ = sess.length > 0
        ? (sess.reduce((acc, s) => acc + (s.avg_quality || 0), 0) / sess.length * 100).toFixed(0) + "%"
        : "—";

      setStats({
        sessions: gam?.session_count || sess.length || 0,
        streak: gam?.streak || 0,
        points: gam?.points || 0,
        quality: avgQ,
      });
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRoadmapGenerated = (res) => {
    setActiveRoadmap(res);
    setShowGenerator(false);
    api.getRoadmapHistory().then(setRoadmapHistory).catch(() => {});
  };

  const handleSwitchRoadmap = async (id) => {
    try {
      await api.activateRoadmap(id);
      await loadData();
    } catch (e) {
      console.error("Failed to activate roadmap:", e);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: "75vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16 }}>
        <div style={{ width: 36, height: 36, borderRadius: "50%", border: `3px solid ${T.primary}`, borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
        <span style={{ fontFamily: T.fontD, fontSize: 11, letterSpacing: "0.15em", color: T.dim, textTransform: "uppercase" }}>
          SYNCHRONIZING ROADMAP INTELLIGENCE…
        </span>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "calc(100vh - 56px)", background: T.bg, paddingBottom: 60 }}>
      {/* ── Quick Ecosystem Action Bar ───────────────────────────────────── */}
      <div
        style={{
          borderBottom: "1px solid rgba(255,255,255,0.05)",
          background: "rgba(19,19,19,0.7)",
          backdropFilter: "blur(12px)",
          padding: "12px 28px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: T.dim, textTransform: "uppercase" }}>STREAK:</span>
            <span style={{ fontFamily: T.fontD, fontSize: 12, fontWeight: 700, color: T.primary }}>🔥 {stats.streak} DAYS</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: T.dim, textTransform: "uppercase" }}>SESSIONS:</span>
            <span style={{ fontFamily: T.fontD, fontSize: 12, fontWeight: 700, color: T.text }}>{stats.sessions} LOGGED</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontFamily: T.fontD, fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: T.dim, textTransform: "uppercase" }}>AVG FORM QUALITY:</span>
            <span style={{ fontFamily: T.fontD, fontSize: 12, fontWeight: 700, color: T.info }}>{stats.quality}</span>
          </div>
        </div>

        {/* Ecosystem Nav Pills */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button
            onClick={() => navigate("/pose")}
            style={{
              padding: "6px 14px",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,0.08)",
              background: T.surface,
              color: T.silver,
              fontFamily: T.fontD,
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: "0.06em",
              cursor: "pointer",
            }}
          >
            📷 FORM CORRECTION
          </button>
          <button
            onClick={() => navigate("/nutrition")}
            style={{
              padding: "6px 14px",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,0.08)",
              background: T.surface,
              color: T.silver,
              fontFamily: T.fontD,
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: "0.06em",
              cursor: "pointer",
            }}
          >
            🥗 NUTRITION TRACKER
          </button>
          <button
            onClick={() => navigate("/coach")}
            style={{
              padding: "6px 14px",
              borderRadius: 8,
              border: "1px solid rgba(0,212,170,0.3)",
              background: "rgba(0,212,170,0.08)",
              color: T.primary,
              fontFamily: T.fontD,
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: "0.06em",
              cursor: "pointer",
            }}
          >
            💬 AI COACH
          </button>
        </div>
      </div>

      {/* ── Main View: Roadmap Generator Wizard or Active Roadmap Viewer ─── */}
      {showGenerator ? (
        <RoadmapGeneratorForm
          onRoadmapGenerated={handleRoadmapGenerated}
          onCancel={activeRoadmap ? () => setShowGenerator(false) : null}
        />
      ) : activeRoadmap ? (
        <RoadmapViewer
          roadmapData={activeRoadmap}
          progress={activeRoadmap.progress || {}}
          onRegenerate={() => setShowGenerator(true)}
          onSwitchRoadmap={handleSwitchRoadmap}
          history={roadmapHistory}
        />
      ) : (
        <div style={{ textAlign: "center", padding: "80px 20px" }}>
          <h2 style={{ fontFamily: T.fontD, fontSize: 28, color: T.text, marginBottom: 12 }}>NO ACTIVE ROADMAP</h2>
          <p style={{ fontFamily: T.fontB, fontSize: 14, color: T.dim, maxWidth: 440, margin: "0 auto 24px" }}>
            Create an AI-tailored multi-week fitness and nutrition roadmap matching your exact training level and dietary preferences.
          </p>
          <button
            onClick={() => setShowGenerator(true)}
            style={{
              padding: "14px 32px",
              borderRadius: 10,
              border: "none",
              background: `linear-gradient(135deg, ${T.primary}, ${T.primaryD})`,
              color: "#131313",
              fontFamily: T.fontD,
              fontSize: 12,
              fontWeight: 700,
              cursor: "pointer",
              textTransform: "uppercase",
            }}
          >
            + BUILD MY FITNESS ROADMAP
          </button>
        </div>
      )}
    </div>
  );
}
