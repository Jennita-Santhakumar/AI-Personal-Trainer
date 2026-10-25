"""
models.py — SQLAlchemy ORM models for the entire platform.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    height_cm: Mapped[Optional[float]] = mapped_column(Float)
    goal: Mapped[Optional[str]] = mapped_column(String(50))   # strength|fat_loss|endurance|flexibility
    level: Mapped[Optional[str]] = mapped_column(String(20))  # beginner|intermediate|advanced
    sport_focus: Mapped[str] = mapped_column(String(50), default="general")
    injuries: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plans: Mapped[list[WorkoutPlan]] = relationship(back_populates="user", cascade="all, delete-orphan")
    roadmaps: Mapped[list[FitnessRoadmap]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list[WorkoutSession]] = relationship(back_populates="user", cascade="all, delete-orphan")
    gamification: Mapped[Optional[GamificationState]] = relationship(back_populates="user", uselist=False)
    personal_records: Mapped[list[PersonalRecord]] = relationship(back_populates="user", cascade="all, delete-orphan")
    oauth_tokens: Mapped[list[OAuthToken]] = relationship(back_populates="user", cascade="all, delete-orphan")


# ── Fitness Roadmaps (AI-Powered Multi-Week Workout & Nutrition Plans) ───────────

class FitnessRoadmap(Base):
    __tablename__ = "fitness_roadmaps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), default="Personalized AI Fitness Roadmap")
    goal: Mapped[str] = mapped_column(String(50))
    level: Mapped[str] = mapped_column(String(50))
    duration_weeks: Mapped[int] = mapped_column(Integer, default=4)
    days_per_week: Mapped[int] = mapped_column(Integer, default=4)
    roadmap_data: Mapped[dict] = mapped_column(JSON, nullable=False)   # Full structured JSON
    progress_data: Mapped[dict] = mapped_column(JSON, default=dict)   # Completed tasks dict
    provider_used: Mapped[str] = mapped_column(String(50), default="auto")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="roadmaps")


# ── Workout plans ─────────────────────────────────────────────────────────────

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    plan_json: Mapped[dict] = mapped_column(JSON, nullable=False)   # full WeeklySplit[]
    goal: Mapped[str] = mapped_column(String(50))
    level: Mapped[str] = mapped_column(String(20))
    weeks: Mapped[int] = mapped_column(Integer, default=4)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="plans")


# ── Workout sessions ──────────────────────────────────────────────────────────

class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    activity: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_minutes: Mapped[Optional[float]] = mapped_column(Float)
    rep_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_quality: Mapped[Optional[float]] = mapped_column(Float)      # 0.0 - 1.0
    perceived_effort: Mapped[Optional[int]] = mapped_column(Integer) # RPE 1-10
    form_violations: Mapped[Optional[dict]] = mapped_column(JSON)    # {"knee_cave": 3}
    metrics: Mapped[Optional[dict]] = mapped_column(JSON)            # calories, distance, avg_hr
    snapshots: Mapped[Optional[list]] = mapped_column(JSON)          # per-rep detail
    notes: Mapped[str] = mapped_column(Text, default="")
    sets_completed: Mapped[int] = mapped_column(Integer, default=0)
    sleep_hours: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_user_date", "user_id", "started_at"),
    )


# ── Personal records ──────────────────────────────────────────────────────────

class PersonalRecord(Base):
    __tablename__ = "personal_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    lift_name: Mapped[str] = mapped_column(String(50))  # squat|bench|deadlift|5k_time
    value: Mapped[float] = mapped_column(Float)          # kg or seconds
    achieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workout_sessions.id"))

    user: Mapped[User] = relationship(back_populates="personal_records")

    __table_args__ = (
        Index("idx_prs_user_lift", "user_id", "lift_name"),
    )


# ── Gamification ──────────────────────────────────────────────────────────────

class GamificationState(Base):
    __tablename__ = "gamification"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    session_count: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_good_form: Mapped[int] = mapped_column(Integer, default=0)
    badges_earned: Mapped[list] = mapped_column(JSON, default=list)
    activities_tried: Mapped[list] = mapped_column(JSON, default=list)
    last_session_date: Mapped[Optional[str]] = mapped_column(String(10))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="gamification")


# ── Coach conversations ───────────────────────────────────────────────────────

class CoachConversation(Base):
    __tablename__ = "coach_conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(10))        # user | assistant
    content: Mapped[str] = mapped_column(Text)
    session_id: Mapped[Optional[str]] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_conv_user_date", "user_id", "created_at"),
    )


# ── OAuth tokens ──────────────────────────────────────────────────────────────

class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(30), primary_key=True)  # fitbit|google_fit|apple
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="oauth_tokens")

    __table_args__ = (
        UniqueConstraint("user_id", "provider"),
    )
