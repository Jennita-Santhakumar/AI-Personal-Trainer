"""
api/routers/wearables.py
OAuth2 flow + data sync for Fitbit and Google Fit.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import httpx, secrets, urllib.parse

from database import get_db
from models import User, OAuthToken
from api.middleware.auth import get_current_user
from features.metrics.tracker import FitbitConnector, GoogleFitConnector
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/v1/wearables", tags=["wearables"])

# ── OAuth state store (use Redis in production) ───────────────────────────────
_oauth_states: dict[str, str] = {}   # state_token -> user_id


# ── Fitbit OAuth ──────────────────────────────────────────────────────────────

FITBIT_AUTH_URL  = "https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_SCOPES    = "activity heartrate sleep"


@router.get("/fitbit/connect")
async def fitbit_connect(user: User = Depends(get_current_user)):
    """Redirect user to Fitbit OAuth consent screen."""
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = user.id
    params = urllib.parse.urlencode({
        "client_id":     settings.fitbit_client_id,
        "response_type": "code",
        "scope":         FITBIT_SCOPES,
        "redirect_uri":  f"{settings.allowed_origins[0]}/api/v1/wearables/fitbit/callback",
        "state":         state,
    })
    return {"auth_url": f"{FITBIT_AUTH_URL}?{params}"}


@router.get("/fitbit/callback")
async def fitbit_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Exchange authorization code for tokens and persist."""
    user_id = _oauth_states.pop(state, None)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    redirect_uri = f"{settings.allowed_origins[0]}/api/v1/wearables/fitbit/callback"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            FITBIT_TOKEN_URL,
            auth=(settings.fitbit_client_id, settings.fitbit_client_secret),
            data={
                "grant_type":   "authorization_code",
                "code":         code,
                "redirect_uri": redirect_uri,
            },
        )
        r.raise_for_status()
        tokens = r.json()

    expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 28800))
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "fitbit")
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.access_token  = tokens["access_token"]
        existing.refresh_token = tokens.get("refresh_token")
        existing.expires_at    = expires_at
    else:
        db.add(OAuthToken(
            user_id=user_id, provider="fitbit",
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            expires_at=expires_at,
        ))
    await db.commit()
    return {"status": "connected", "provider": "fitbit"}


async def _refresh_fitbit_token(token_row: OAuthToken, db: AsyncSession) -> str:
    """Refresh an expired Fitbit token. Returns new access token."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            FITBIT_TOKEN_URL,
            auth=(settings.fitbit_client_id, settings.fitbit_client_secret),
            data={"grant_type": "refresh_token", "refresh_token": token_row.refresh_token},
        )
        r.raise_for_status()
        tokens = r.json()
    token_row.access_token  = tokens["access_token"]
    token_row.refresh_token = tokens.get("refresh_token", token_row.refresh_token)
    token_row.expires_at    = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 28800))
    await db.commit()
    return token_row.access_token


@router.post("/fitbit/sync")
async def fitbit_sync(
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Pull one day of Fitbit data. date defaults to today (YYYY-MM-DD)."""
    date = date or datetime.utcnow().date().isoformat()
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user.id, OAuthToken.provider == "fitbit")
    )
    token_row = result.scalar_one_or_none()
    if not token_row:
        raise HTTPException(status_code=400, detail="Fitbit not connected. Call /fitbit/connect first.")

    # Auto-refresh if expired
    access_token = token_row.access_token
    if token_row.expires_at and token_row.expires_at < datetime.utcnow():
        access_token = await _refresh_fitbit_token(token_row, db)

    connector = FitbitConnector(access_token)
    try:
        data = await connector.get_daily_summary(date)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Fitbit API error: {e.response.text}")

    return {"date": date, "source": "fitbit", "data": data}


@router.get("/fitbit/status")
async def fitbit_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user.id, OAuthToken.provider == "fitbit")
    )
    token = result.scalar_one_or_none()
    if not token:
        return {"connected": False}
    return {
        "connected": True,
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
        "needs_refresh": bool(token.expires_at and token.expires_at < datetime.utcnow()),
    }


# ── Google Fit OAuth ──────────────────────────────────────────────────────────

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES    = " ".join([
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
])


@router.get("/google-fit/connect")
async def google_fit_connect(user: User = Depends(get_current_user)):
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = user.id
    redirect_uri = f"{settings.allowed_origins[0]}/api/v1/wearables/google-fit/callback"
    params = urllib.parse.urlencode({
        "client_id":     settings.google_fit_client_id,
        "redirect_uri":  redirect_uri,
        "response_type": "code",
        "scope":         GOOGLE_SCOPES,
        "access_type":   "offline",
        "state":         state,
    })
    return {"auth_url": f"{GOOGLE_AUTH_URL}?{params}"}


@router.get("/google-fit/callback")
async def google_fit_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    user_id = _oauth_states.pop(state, None)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    redirect_uri = f"{settings.allowed_origins[0]}/api/v1/wearables/google-fit/callback"
    async with httpx.AsyncClient() as client:
        r = await client.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     settings.google_fit_client_id,
            "client_secret": settings.google_fit_client_secret,
            "redirect_uri":  redirect_uri,
            "grant_type":    "authorization_code",
        })
        r.raise_for_status()
        tokens = r.json()

    expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "google_fit")
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.access_token  = tokens["access_token"]
        existing.refresh_token = tokens.get("refresh_token", existing.refresh_token)
        existing.expires_at    = expires_at
    else:
        db.add(OAuthToken(
            user_id=user_id, provider="google_fit",
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            expires_at=expires_at,
        ))
    await db.commit()
    return {"status": "connected", "provider": "google_fit"}


@router.post("/google-fit/sync")
async def google_fit_sync(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Sync last N days of Google Fit step + HR data."""
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user.id, OAuthToken.provider == "google_fit")
    )
    token_row = result.scalar_one_or_none()
    if not token_row:
        raise HTTPException(status_code=400, detail="Google Fit not connected")

    connector = GoogleFitConnector(token_row.access_token)
    end   = datetime.utcnow()
    start = end - timedelta(days=days)
    try:
        steps_data = await connector.get_aggregate(start, end, "steps")
        hr_data    = await connector.get_aggregate(start, end, "heart_rate")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Google Fit API error: {e.response.text}")

    return {"source": "google_fit", "days": days, "steps": steps_data, "heart_rate": hr_data}


@router.get("/connected")
async def list_connected(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all wearable providers and their connection status."""
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user.id)
    )
    tokens = result.scalars().all()
    connected = {t.provider: {"connected": True, "expires_at": t.expires_at.isoformat() if t.expires_at else None}
                 for t in tokens}
    for provider in ("fitbit", "google_fit", "apple"):
        if provider not in connected:
            connected[provider] = {"connected": False}
    return connected


@router.delete("/{provider}/disconnect")
async def disconnect_provider(
    provider: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user.id, OAuthToken.provider == provider)
    )
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail=f"{provider} not connected")
    await db.delete(token)
    await db.commit()
    return {"status": "disconnected", "provider": provider}
