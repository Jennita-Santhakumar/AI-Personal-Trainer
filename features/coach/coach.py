"""
features/coach/coach.py

Provider priority:
  1. Groq  — if GROQ_API_KEY is set (~800 tok/s, free tier, llama3.1-8b-instant)
  2. Ollama — local fallback (no API key needed, slower on CPU)

Groq uses the same OpenAI-compatible /v1/chat/completions endpoint,
so the streaming logic is identical for both providers.
"""
from __future__ import annotations
from typing import AsyncGenerator, List, Dict, Optional
from datetime import datetime
import json as _json
import asyncio

import httpx

from config import get_settings
from features.coach.memory import UserCoachProfile, WorkoutMemory, VectorMemoryStore
from features.coach.prompts import SYSTEM_PROMPT, USER_CONTEXT_TEMPLATE, TEMPLATES

settings = get_settings()

# ── Provider config ───────────────────────────────────────────────────────────

GROQ_API_BASE = "https://api.groq.com/openai/v1"
GROQ_MODEL    = "llama-3.1-8b-instant"   # fast, free-tier friendly
OLLAMA_MODEL  = settings.coach_model


def _use_groq() -> bool:
    return bool(getattr(settings, "groq_api_key", ""))


def _chat_url() -> str:
    if _use_groq():
        return GROQ_API_BASE + "/chat/completions"
    return settings.ollama_url.rstrip("/") + "/v1/chat/completions"


def _auth_headers() -> dict:
    if _use_groq():
        return {"Authorization": f"Bearer {settings.groq_api_key}"}
    return {}


def _model_name() -> str:
    return GROQ_MODEL if _use_groq() else OLLAMA_MODEL


def _ollama_base() -> str:
    return settings.ollama_url.rstrip("/")


# ── Shared HTTP client ────────────────────────────────────────────────────────

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _client


# ── Ollama model management ───────────────────────────────────────────────────

async def ensure_model_pulled() -> bool:
    """Pull Ollama model if not already available. No-op when using Groq."""
    if _use_groq():
        return True
    try:
        client = _get_client()
        r = await client.get(_ollama_base() + "/api/tags", timeout=5.0)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            model_base = OLLAMA_MODEL.split(":")[0]
            if any(model_base in m for m in models):
                return True
        asyncio.create_task(_pull_model_background())
        return False
    except Exception:
        return False


async def _pull_model_background():
    try:
        client = _get_client()
        await client.post(
            _ollama_base() + "/api/pull",
            json={"name": OLLAMA_MODEL},
            timeout=httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=5.0),
        )
    except Exception as e:
        print(f"[coach] Background model pull failed: {e}")


# ── AICoach ───────────────────────────────────────────────────────────────────

class AICoach:
    MAX_TURNS = 6

    def __init__(self):
        try:
            self.vector = VectorMemoryStore(settings.vector_memory_dir)
            self._has_vector = True
        except Exception as e:
            print(f"[coach] VectorMemoryStore unavailable: {e}")
            self.vector = None
            self._has_vector = False

        self._history: List[Dict[str, str]] = []

    def _build_context_prefix(
        self,
        profile: UserCoachProfile,
        query: str,
        session: Optional[WorkoutMemory] = None,
    ) -> str:
        past_block = "None yet."
        if self._has_vector and self.vector:
            try:
                past = self.vector.retrieve(profile.user_id, query, n=2)
                past_block = "\n".join(f"- {p}" for p in past) if past else "None yet."
            except Exception:
                pass

        recent = profile.recent_workouts(2)
        recent_text = (
            "\n".join(f"  {w.summary_str()}" for w in recent) or "No recent sessions."
        )
        session_text = "None." if not session else (
            f"Activity: {session.activity}, RPE: {session.perceived_effort or '?'}/10, "
            f"Quality: {f'{session.quality_score:.0%}' if session.quality_score else 'N/A'}"
        )
        avg_q = profile.avg_quality_recent()
        return USER_CONTEXT_TEMPLATE.format(
            name=profile.name,
            goal=profile.goal,
            level=profile.level,
            week=profile.current_program_week,
            streak=profile.consecutive_days_trained,
            injuries=", ".join(profile.injuries) or "None",
            prs=profile.pr_context(),
            n_recent=2,
            recent_sessions=recent_text,
            form_issues=", ".join(profile.common_form_issues()) or "None detected",
            avg_quality=f"{avg_q:.0%}" if avg_q else "Not enough data",
            todays_session=session_text,
            past_advice=past_block,
        )

    def _build_messages(self, user_msg: str) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in self._history[-(self.MAX_TURNS * 2):]:
            messages.append(turn)
        messages.append({"role": "user", "content": user_msg})
        return messages

    async def chat(
        self,
        message: str,
        profile: UserCoachProfile,
        session: Optional[WorkoutMemory] = None,
    ) -> AsyncGenerator[str, None]:
        context_prefix = self._build_context_prefix(profile, message, session)
        full_user_msg = f"{context_prefix}\n\n---\n\nUser: {message}"
        messages = self._build_messages(full_user_msg)

        provider = "Groq" if _use_groq() else "Ollama"
        print(f"[coach] Using provider: {provider} / model: {_model_name()}")

        # Groq free tier has a ~6000 token request limit.
        # Truncate the context prefix if the message is too long.
        MAX_CHARS = 12000
        if len(full_user_msg) > MAX_CHARS:
            trimmed_prefix = context_prefix[:(MAX_CHARS - len(message) - 200)]
            full_user_msg = f"{trimmed_prefix}\n\n---\n\nUser: {message}"
            messages = self._build_messages(full_user_msg)
            print(f"[coach] Prompt trimmed to {len(full_user_msg)} chars")


        full_response = ""
        payload = {
            "model": _model_name(),
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7,
            "stream": True,
        }

        try:
            client = _get_client()
            async with client.stream(
                "POST", _chat_url(),
                json=payload,
                headers=_auth_headers(),
            ) as resp:
                if resp.status_code == 404 and not _use_groq():
                    asyncio.create_task(_pull_model_background())
                    yield ("The AI model is downloading for the first time (~4.7 GB). "
                           "This runs in the background — please try again in a few minutes.")
                    return
                if resp.status_code == 401:
                    yield "Groq API key is invalid. Check GROQ_API_KEY in your .env file."
                    return
                if resp.status_code == 429:
                    yield "[Rate limited — switching to local Ollama...] "
                    async for chunk in self._ollama_fallback(messages):
                        full_response += chunk
                        yield chunk
                    # persist & return after fallback
                    if full_response:
                        self._history.append({"role": "user", "content": full_user_msg})
                        self._history.append({"role": "assistant", "content": full_response})
                    return
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = _json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            full_response += delta
                            yield delta
                    except (_json.JSONDecodeError, KeyError, IndexError):
                        continue

        except httpx.ConnectError:
            if _use_groq():
                yield "Cannot reach Groq API. Check your internet connection."
            else:
                yield "Ollama is starting up. Please wait 30 seconds and try again."
            return
        except httpx.TimeoutException:
            yield "Response timed out. Please try again."
            return
        except Exception as e:
            yield f"Coach error: {str(e)}"
            return

        if not full_response:
            return

        self._history.append({"role": "user", "content": full_user_msg})
        self._history.append({"role": "assistant", "content": full_response})

        if self._has_vector and self.vector:
            try:
                self.vector.store(profile.user_id, "user", message)
                self.vector.store(
                    profile.user_id, "assistant", full_response,
                    metadata={"date": datetime.utcnow().date().isoformat()},
                )
            except Exception:
                pass

    async def _ollama_fallback(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """Stream from Ollama when Groq rate-limits."""
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7,
            "stream": True,
        }
        try:
            client = _get_client()
            ollama_url = settings.ollama_url.rstrip("/") + "/v1/chat/completions"
            async with client.stream("POST", ollama_url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = _json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except (_json.JSONDecodeError, KeyError, IndexError):
                        continue
        except Exception as e:
            yield f"[Ollama fallback error: {e}]"

    async def _single_call_async(self, prompt: str, max_tokens: int = 512) -> str:
        payload = {
            "model": _model_name(),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False,
        }
        try:
            client = _get_client()
            resp = await client.post(
                _chat_url(), json=payload, headers=_auth_headers(),
            )
            if resp.status_code == 404 and not _use_groq():
                asyncio.create_task(_pull_model_background())
                return "[Model downloading — try again in a few minutes]"
            if resp.status_code == 429:
                return "[Groq rate limit — try again shortly]"
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except httpx.ConnectError:
            return "[Connection error — check your network or Ollama status]"
        except Exception as e:
            return f"[Unavailable: {e}]"

    async def daily_briefing_async(self, profile: UserCoachProfile) -> str:
        last = profile.recent_workouts(1)
        prompt = TEMPLATES["daily_briefing"].format(
            name=profile.name,
            week=profile.current_program_week,
            last_session=last[0].activity if last else "none yet",
            streak=profile.consecutive_days_trained,
            form_issues=profile.common_form_issues() or "none",
        )
        return await self._single_call_async(prompt, max_tokens=256)

    def reset_conversation(self):
        self._history.clear()
