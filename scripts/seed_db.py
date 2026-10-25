"""
scripts/seed_db.py — seed a demo user account on first run.
Idempotent: safe to run multiple times.
"""
import asyncio
import httpx
import sys

API_URL = "http://api:8000"
DEMO_EMAIL = "demo@fitnessplatform.com"
DEMO_PASSWORD = "Demo1234!"
DEMO_NAME = "Demo Athlete"


async def seed():
    async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
        # Try to login first — if it works, user already exists
        try:
            r = await client.post("/api/v1/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
            if r.status_code == 200:
                print("[seed] Demo user already exists — skipping.")
                return
        except Exception:
            pass

        # Register demo user
        try:
            r = await client.post("/api/v1/auth/register", json={
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD,
                "name": DEMO_NAME,
                "goal": "strength",
                "level": "intermediate",
                "age": 24,
                "weight_kg": 68.0,
                "height_cm": 168.0,
            })
            if r.status_code == 201:
                print(f"[seed] Demo user created: {DEMO_EMAIL} / {DEMO_PASSWORD}")
            else:
                print(f"[seed] Register returned {r.status_code}: {r.text}")
        except Exception as e:
            print(f"[seed] Error creating demo user: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed())
