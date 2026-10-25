"""
features/metrics/tracker.py — fitness metrics: calorie estimation, GPS, wearable connectors.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
import math


@dataclass
class GPSPoint:
    lat: float
    lng: float
    elevation_m: float = 0.0
    timestamp: Optional[datetime] = None


@dataclass
class MetricsSnapshot:
    timestamp: datetime
    heart_rate_bpm: Optional[int] = None
    steps: Optional[int] = None
    calories_burned: Optional[float] = None
    distance_km: Optional[float] = None
    pace_min_per_km: Optional[float] = None
    cadence_spm: Optional[int] = None
    elevation_gain_m: Optional[float] = None
    power_watts: Optional[int] = None
    source: str = "manual"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class CalorieEstimator:
    MET_VALUES = {
        "running_easy": 8.0, "running_tempo": 10.5, "running_interval": 12.0,
        "walking": 3.5, "swimming_easy": 6.0, "swimming_hard": 9.8,
        "yoga": 3.0, "yoga_power": 4.0, "squat": 5.0, "deadlift": 6.0,
        "bench": 3.5, "plank": 4.0, "hiit": 10.0, "cycling": 7.0,
        "rowing": 7.0, "powerlifting": 5.5,
    }

    def estimate_met(self, activity: str, intensity: str = "moderate") -> float:
        key = f"{activity.lower().replace(' ', '_')}_{intensity.lower()}"
        if key in self.MET_VALUES:
            return self.MET_VALUES[key]
        for k, v in self.MET_VALUES.items():
            if activity.lower().split("_")[0] in k:
                return v
        return 4.0

    def calories_from_met(self, met: float, weight_kg: float, duration_minutes: float) -> float:
        return round(met * weight_kg * (duration_minutes / 60), 1)

    def calories_from_hr(self, avg_hr: float, age: int, weight_kg: float,
                          duration_minutes: float, is_male: bool = True) -> float:
        """Keytel et al. formula — more accurate when HR data available."""
        if is_male:
            cal_pm = (-55.0969 + 0.6309 * avg_hr + 0.1988 * weight_kg + 0.2017 * age) / 4.184
        else:
            cal_pm = (-20.4022 + 0.4472 * avg_hr - 0.1263 * weight_kg + 0.074 * age) / 4.184
        return round(max(0.0, cal_pm * duration_minutes), 1)


class GPSProcessor:
    @staticmethod
    def haversine_km(p1: GPSPoint, p2: GPSPoint) -> float:
        R = 6371.0
        lat1, lat2 = math.radians(p1.lat), math.radians(p2.lat)
        dlat = math.radians(p2.lat - p1.lat)
        dlng = math.radians(p2.lng - p1.lng)
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))

    def total_distance_km(self, track: List[GPSPoint]) -> float:
        if len(track) < 2:
            return 0.0
        return round(sum(self.haversine_km(track[i], track[i + 1]) for i in range(len(track) - 1)), 3)

    def pace_min_per_km(self, distance_km: float, duration_seconds: float) -> float:
        if distance_km <= 0:
            return 0.0
        return round((duration_seconds / 60) / distance_km, 2)

    def elevation_gain_m(self, track: List[GPSPoint]) -> float:
        gain = sum(
            max(0.0, track[i].elevation_m - track[i - 1].elevation_m)
            for i in range(1, len(track))
        )
        return round(gain, 1)


class FitbitConnector:
    """Fitbit Web API v1 connector (requires valid OAuth2 access token)."""
    BASE_URL = "https://api.fitbit.com/1/user/-"

    def __init__(self, access_token: str):
        self._headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

    async def get_daily_summary(self, date: str) -> dict:
        """date: YYYY-MM-DD. Returns steps, calories, distance, HR."""
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            act_r = await client.get(f"{self.BASE_URL}/activities/date/{date}.json", headers=self._headers)
            hr_r  = await client.get(f"{self.BASE_URL}/activities/heart/date/{date}/1d.json", headers=self._headers)
            act_r.raise_for_status()
            hr_r.raise_for_status()
            s = act_r.json()["summary"]
            hr = hr_r.json()["activities-heart"][0]["value"]
            return {
                "steps": s.get("steps", 0),
                "calories": s.get("caloriesOut", 0),
                "distance_km": round(s.get("distances", [{}])[0].get("distance", 0) * 1.60934, 2),
                "active_minutes": s.get("veryActiveMinutes", 0) + s.get("fairlyActiveMinutes", 0),
                "resting_hr": hr.get("restingHeartRate"),
                "hr_zones": hr.get("heartRateZones", []),
            }

    async def get_intraday_hr(self, date: str) -> List[dict]:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{self.BASE_URL}/activities/heart/date/{date}/1d/1min.json",
                headers=self._headers
            )
            r.raise_for_status()
            return r.json()["activities-heart-intraday"]["dataset"]


class GoogleFitConnector:
    """Google Fit REST API connector."""
    BASE_URL = "https://www.googleapis.com/fitness/v1/users/me"
    DATA_SOURCES = {
        "steps":      "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps",
        "calories":   "derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended",
        "heart_rate": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm",
    }

    def __init__(self, access_token: str):
        self._headers = {"Authorization": f"Bearer {access_token}"}

    async def get_aggregate(self, start: datetime, end: datetime, metric: str) -> dict:
        import httpx
        source = self.DATA_SOURCES.get(metric, "")
        body = {
            "aggregateBy": [{"dataSourceId": source}],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": int(start.timestamp() * 1000),
            "endTimeMillis": int(end.timestamp() * 1000),
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{self.BASE_URL}/dataset:aggregate",
                                  headers=self._headers, json=body)
            r.raise_for_status()
            return r.json()


class SimulatedSensor:
    """Estimates metrics from webcam motion or phone accelerometer — no wearable needed."""
    def __init__(self, height_m: float, weight_kg: float):
        self.height = height_m
        self.weight = weight_kg
        self.step_length_m = height_m * 0.413

    def steps_to_distance_km(self, steps: int) -> float:
        return round((steps * self.step_length_m) / 1000, 3)

    def estimate_hr_from_breathing(self, breathing_rate_bpm: float) -> int:
        """HR ≈ 4 × breathing rate. Breathing detectable from shoulder movement."""
        return int(min(200, max(50, breathing_rate_bpm * 4)))

    def estimate_steps_from_ankle_velocity(self, pose_history: List[dict]) -> int:
        """Count step cycles from ankle joint Y-velocity peaks."""
        if len(pose_history) < 2:
            return 0
        ankle_y = [p.get("LEFT_ANKLE", [0, 0])[1] for p in pose_history]
        steps, direction = 0, None
        for i in range(1, len(ankle_y)):
            delta = ankle_y[i] - ankle_y[i - 1]
            if direction == "down" and delta > 0.002:
                steps += 1
                direction = "up"
            elif delta < -0.002:
                direction = "down"
        return steps
