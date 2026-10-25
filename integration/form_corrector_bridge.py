"""
integration/form_corrector_bridge.py
Drop-in bridge between your existing form corrector and the new platform.
Collects per-rep events and flushes the full session to the platform API on exit.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Callable, Dict
import asyncio, uuid


@dataclass
class RepEvent:
    session_id: str
    rep_number: int
    activity: str
    violations: List[str]
    quality_score: Optional[float]
    features: dict
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class PlatformBridge:
    """
    Wire this into your existing run.py in four lines:

        bridge = PlatformBridge(api_base, token, user_id)
        # after each rep:
        bridge.on_rep(activity, violations, quality, features)
        # on Q key press:
        asyncio.run(bridge.flush(perceived_effort=8))
    """

    def __init__(self, api_base: str, auth_token: str, user_id: str):
        self.api_base   = api_base.rstrip("/")
        self.token      = auth_token
        self.user_id    = user_id
        self.session_id = str(uuid.uuid4())
        self._events: List[RepEvent] = []
        self._started_at = datetime.utcnow().isoformat()
        self._on_badge: Optional[Callable] = None
        self._new_prs: Dict[str, float] = {}

    def on_rep(self, activity: str, violations: List[str],
               quality: Optional[float], features: dict):
        """Call once per completed rep from your RepCounter callback."""
        self._events.append(RepEvent(
            session_id=self.session_id,
            rep_number=len(self._events) + 1,
            activity=activity,
            violations=violations,
            quality_score=quality,
            features=features,
        ))

    def register_pr(self, lift: str, value_kg: float):
        """Call when a new personal record is detected during the session."""
        self._new_prs[lift] = value_kg

    def register_badge_callback(self, fn: Callable):
        """Optional: fn(badge_dict) called after flush to show badge popups."""
        self._on_badge = fn

    async def flush(
        self,
        notes: str = "",
        perceived_effort: Optional[int] = None,
        sleep_hours: Optional[float] = None,
        run_distance_km: Optional[float] = None,
    ) -> str:
        """Flush the session to the platform API. Returns coach feedback string."""
        import httpx

        if not self._events:
            return "No reps recorded."

        activity = self._events[0].activity
        violations_agg: Dict[str, int] = {}
        quality_sum, quality_n = 0.0, 0
        for ev in self._events:
            for v in ev.violations:
                violations_agg[v] = violations_agg.get(v, 0) + 1
            if ev.quality_score is not None:
                quality_sum += ev.quality_score
                quality_n += 1

        avg_quality = round(quality_sum / quality_n, 3) if quality_n else None
        metrics: dict = {}
        if run_distance_km:
            metrics["distance_km"] = run_distance_km

        payload = {
            "activity": activity,
            "started_at": self._started_at,
            "ended_at": datetime.utcnow().isoformat(),
            "rep_count": len(self._events),
            "avg_quality": avg_quality,
            "perceived_effort": perceived_effort,
            "form_violations": violations_agg,
            "metrics": metrics,
            "sets_completed": len(self._events),
            "sleep_hours": sleep_hours,
            "notes": notes,
            "new_prs": self._new_prs,
            "snapshots": [
                {"rep": e.rep_number, "timestamp": e.timestamp,
                 "violations": e.violations, "quality": e.quality_score}
                for e in self._events
            ],
        }

        headers = {"Authorization": f"Bearer {self.token}"}
        coach_response = ""

        async with httpx.AsyncClient(timeout=15) as client:
            # 1. Save session
            r = await client.post(f"{self.api_base}/api/v1/sessions/", json=payload, headers=headers)
            r.raise_for_status()
            session_id = r.json().get("session_id", self.session_id)

            # 2. Get coach feedback
            coach_r = await client.post(
                f"{self.api_base}/api/v1/coach/message",
                json={"message": (
                    f"I just finished a {activity} session: {len(self._events)} reps, "
                    f"avg quality {f'{avg_quality:.0%}' if avg_quality else 'N/A'}, "
                    f"RPE {perceived_effort or '?'}/10. "
                    f"Form issues: {list(violations_agg.keys()) or 'none'}. "
                    "Give me brief post-session feedback."
                ), "session_id": session_id},
                headers=headers,
            )
            if coach_r.status_code == 200:
                coach_response = coach_r.json().get("response", "")

            # 3. Check for new badges
            gam_r = await client.get(f"{self.api_base}/api/v1/gamification/status", headers=headers)
            if gam_r.status_code == 200 and self._on_badge:
                badges = gam_r.json().get("badges", [])
                for b in badges:
                    if b.get("earned"):
                        self._on_badge(b)

        return coach_response
