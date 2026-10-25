"""
features/coach/memory.py — coach memory data structures and vector store.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from collections import Counter
import uuid

try:
    import chromadb
except ImportError:
    chromadb = None


@dataclass
class WorkoutMemory:
    session_id: str
    date: str
    activity: str
    reps_completed: Dict[str, int] = field(default_factory=dict)
    weights_used: Dict[str, float] = field(default_factory=dict)
    form_violations: List[str] = field(default_factory=list)
    quality_score: Optional[float] = None
    perceived_effort: Optional[int] = None
    sets_completed: int = 0
    notes: str = ""

    def summary_str(self) -> str:
        return (
            f"{self.date} ({self.activity}): "
            f"quality={f'{self.quality_score:.0%}' if self.quality_score else 'N/A'} "
            f"RPE={self.perceived_effort or '?'} "
            f"violations={self.form_violations or []}"
        )


@dataclass
class UserCoachProfile:
    user_id: str
    name: str
    goal: str
    level: str
    injuries: List[str] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)
    workout_history: List[WorkoutMemory] = field(default_factory=list)
    personal_records: Dict[str, float] = field(default_factory=dict)
    current_program_week: int = 1
    consecutive_days_trained: int = 0
    last_session_date: Optional[str] = None

    def recent_workouts(self, n: int = 5) -> List[WorkoutMemory]:
        return self.workout_history[-n:]

    def pr_context(self) -> str:
        if not self.personal_records:
            return "No PRs recorded yet"
        return ", ".join(f"{k}: {v}kg" for k, v in self.personal_records.items())

    def common_form_issues(self, sessions: int = 10) -> List[str]:
        all_v = []
        for w in self.workout_history[-sessions:]:
            all_v.extend(w.form_violations)
        counter = Counter(all_v)
        return [k for k, v in counter.most_common(3) if v >= 2]

    def avg_quality_recent(self, n: int = 5) -> Optional[float]:
        qs = [w.quality_score for w in self.workout_history[-n:] if w.quality_score is not None]
        return round(sum(qs) / len(qs), 3) if qs else None


class VectorMemoryStore:
    """
    Persistent semantic memory using ChromaDB with graceful in-memory fallback.
    Each coaching turn is embedded and stored per user.
    """

    def __init__(self, persist_dir: str = "./coach_memory"):
        self.persist_dir = persist_dir
        if chromadb:
            try:
                self.client = chromadb.PersistentClient(path=persist_dir)
            except Exception:
                self.client = None
        else:
            self.client = None
        self._fallback_store: Dict[str, List[str]] = {}

    def _collection(self, user_id: str):
        if not self.client:
            return None
        return self.client.get_or_create_collection(
            name=f"user_{user_id.replace('-', '_')}",
            metadata={"hnsw:space": "cosine"},
        )

    def store(self, user_id: str, role: str, content: str, metadata: Optional[dict] = None):
        col = self._collection(user_id)
        if col:
            col.add(
                documents=[content],
                ids=[str(uuid.uuid4())],
                metadatas=[{"role": role, "ts": datetime.utcnow().isoformat(), **(metadata or {})}],
            )
        else:
            if user_id not in self._fallback_store:
                self._fallback_store[user_id] = []
            self._fallback_store[user_id].append(content)

    def retrieve(self, user_id: str, query: str, n: int = 5) -> List[str]:
        col = self._collection(user_id)
        if col:
            count = col.count()
            if count == 0:
                return []
            results = col.query(query_texts=[query], n_results=min(n, count))
            return results["documents"][0] if results["documents"] else []
        return self._fallback_store.get(user_id, [])[-n:]

    def clear(self, user_id: str):
        if self.client:
            try:
                self.client.delete_collection(f"user_{user_id.replace('-', '_')}")
            except Exception:
                pass
        self._fallback_store.pop(user_id, None)
