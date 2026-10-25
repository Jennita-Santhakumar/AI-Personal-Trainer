"""
ml/models/injury_risk.py
Random Forest classifier for injury risk prediction.
Features: training load metrics + form quality trends.
"""
from __future__ import annotations
import numpy as np
import pickle
from pathlib import Path
from typing import List, Optional


FEATURE_NAMES = [
    "weekly_volume_delta",       # % change in sets vs previous week
    "avg_rpe_last_7",            # average RPE last 7 sessions
    "consecutive_hard_sessions", # sessions in a row with RPE >= 8
    "avg_quality_last_7",        # average form quality score
    "form_violation_rate",       # violations per session (recent)
    "sleep_deficit",             # sessions with sleep < 6h this week
    "days_trained_this_week",    # raw count
    "age_factor",                # age / 40 (normalised)
    "streak",                    # current streak days
]


class InjuryRiskModel:
    """
    Sklearn RandomForestClassifier wrapper.
    Predicts: 0 = low risk, 1 = moderate risk, 2 = high risk.
    """

    MODEL_PATH = Path(__file__).parent / "injury_risk_rf.pkl"

    def __init__(self):
        self._model = None

    def build_features(self, session_history: List[dict], user_age: int = 25,
                        streak: int = 0) -> np.ndarray:
        if not session_history:
            return np.zeros((1, len(FEATURE_NAMES)))

        recent = session_history[-14:]
        this_week  = [s for s in recent[-7:]]
        prev_week  = [s for s in recent[:7]]

        vol_this  = sum(s.get("sets_completed", 0) for s in this_week)
        vol_prev  = sum(s.get("sets_completed", 0) for s in prev_week)
        vol_delta = (vol_this - vol_prev) / max(vol_prev, 1)

        rpe_vals = [s.get("perceived_effort", 6) for s in this_week if s.get("perceived_effort")]
        avg_rpe  = np.mean(rpe_vals) if rpe_vals else 6.0

        consec = 0
        for s in reversed(recent):
            if (s.get("perceived_effort") or 0) >= 8:
                consec += 1
            else:
                break

        q_vals = [s.get("avg_quality", 0.7) for s in this_week if s.get("avg_quality")]
        avg_q  = np.mean(q_vals) if q_vals else 0.7

        violations = [len(s.get("form_violations", [])) for s in this_week]
        vio_rate   = np.mean(violations) if violations else 0.0

        sleep_def = sum(1 for s in this_week if (s.get("sleep_hours") or 7) < 6)

        features = np.array([[
            vol_delta,
            avg_rpe,
            consec,
            avg_q,
            vio_rate,
            sleep_def,
            len(this_week),
            min(user_age / 40.0, 1.5),
            min(streak / 30.0, 1.0),
        ]])
        return features

    def predict(self, features: np.ndarray) -> tuple[int, float]:
        """Returns (risk_class, confidence). Falls back to heuristic if no model."""
        if self._model is None and not self.MODEL_PATH.exists():
            return self._heuristic(features)
        if self._model is None:
            self._load()
        probs = self._model.predict_proba(features)[0]
        risk_class = int(np.argmax(probs))
        return risk_class, float(probs[risk_class])

    def _heuristic(self, features: np.ndarray) -> tuple[int, float]:
        """Rule-based fallback — used before model is trained."""
        f = features[0]
        vol_delta, avg_rpe, consec, avg_q, vio_rate = f[0], f[1], f[2], f[3], f[4]
        score = 0
        if vol_delta > 0.3:  score += 2
        if avg_rpe > 8.0:    score += 2
        if consec >= 4:      score += 2
        if avg_q < 0.6:      score += 1
        if vio_rate > 2:     score += 1
        if score >= 4:       return 2, 0.85
        if score >= 2:       return 1, 0.70
        return 0, 0.80

    def _load(self):
        with open(self.MODEL_PATH, "rb") as f:
            self._model = pickle.load(f)

    def save(self, model):
        self._model = model
        with open(self.MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        print(f"Model saved → {self.MODEL_PATH}")

    RISK_LABELS = {0: "low", 1: "moderate", 2: "high"}

    def risk_label(self, risk_class: int) -> str:
        return self.RISK_LABELS.get(risk_class, "unknown")
