"""
tests/integration/test_api.py
End-to-end API integration tests using httpx AsyncClient + in-memory SQLite.
Run with: pytest tests/integration/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Use an in-memory SQLite DB for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class TestBase(DeclarativeBase):
    pass


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def test_app():
    """Create app with overridden in-memory DB."""
    import os
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"]   = "test-secret-key"
    os.environ["APP_ENV"]      = "test"

    from database import Base, get_db
    from main import create_app

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestSession = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with TestSession() as session:
            yield session
            await session.commit()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    yield app

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(client):
    """Client with a registered + logged-in user."""
    reg = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "name": "Test User",
        "goal": "strength",
        "level": "intermediate",
        "age": 28,
        "weight_kg": 80.0,
        "height_cm": 178.0,
    })
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


# ── Auth tests ────────────────────────────────────────────────────────────────

class TestAuth:
    async def test_register_success(self, client):
        r = await client.post("/api/v1/auth/register", json={
            "email": "new@example.com", "password": "Pass1234!",
            "name": "New User", "goal": "endurance", "level": "beginner",
            "age": 22, "weight_kg": 65.0, "height_cm": 170.0,
        })
        assert r.status_code == 201
        assert "access_token" in r.json()

    async def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "password": "Pass1234!",
                   "name": "X", "goal": "strength", "level": "beginner",
                   "age": 25, "weight_kg": 70.0, "height_cm": 175.0}
        await client.post("/api/v1/auth/register", json=payload)
        r = await client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 400

    async def test_login_success(self, auth_client):
        r = await auth_client.post("/api/v1/auth/login",
                                   json={"email": "test@example.com", "password": "TestPass123!"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    async def test_login_wrong_password(self, client):
        r = await client.post("/api/v1/auth/login",
                              json={"email": "test@example.com", "password": "wrong"})
        assert r.status_code == 401

    async def test_get_me_authenticated(self, auth_client):
        r = await auth_client.get("/api/v1/auth/me")
        assert r.status_code == 200
        assert r.json()["email"] == "test@example.com"

    async def test_get_me_unauthenticated(self, client):
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 403


# ── Plan tests ────────────────────────────────────────────────────────────────

class TestPlans:
    async def test_generate_plan(self, auth_client):
        r = await auth_client.post("/api/v1/plans/generate", json={
            "goal": "strength", "level": "intermediate",
            "days_per_week": 4, "weeks": 2,
        })
        assert r.status_code == 201
        data = r.json()
        assert "plan_id" in data
        assert len(data["weeks"]) == 2

    async def test_generate_plan_with_injuries(self, auth_client):
        r = await auth_client.post("/api/v1/plans/generate", json={
            "goal": "strength", "level": "beginner",
            "days_per_week": 3, "injuries": ["lower_back"], "weeks": 1,
        })
        assert r.status_code == 201
        weeks = r.json()["weeks"]
        for week in weeks:
            for day in week["days"]:
                names = [e["name"].lower() for e in day["exercises"]]
                assert not any("conventional deadlift" in n for n in names)

    async def test_get_current_plan(self, auth_client):
        await auth_client.post("/api/v1/plans/generate", json={
            "goal": "endurance", "level": "beginner", "days_per_week": 3, "weeks": 1
        })
        r = await auth_client.get("/api/v1/plans/current")
        assert r.status_code == 200
        assert r.json()["goal"] == "endurance"

    async def test_get_current_plan_none(self, auth_client):
        r = await auth_client.get("/api/v1/plans/current")
        assert r.status_code in (200, 404)

    async def test_all_goals_generate(self, auth_client):
        for goal in ("strength", "fat_loss", "endurance", "flexibility", "hybrid"):
            r = await auth_client.post("/api/v1/plans/generate", json={
                "goal": goal, "level": "beginner", "days_per_week": 3, "weeks": 1
            })
            assert r.status_code == 201, f"Failed for goal={goal}: {r.text}"


# ── Session tests ─────────────────────────────────────────────────────────────

class TestSessions:
    async def test_submit_session(self, auth_client):
        r = await auth_client.post("/api/v1/sessions/", json={
            "activity": "squat",
            "rep_count": 20,
            "avg_quality": 0.82,
            "perceived_effort": 7,
            "form_violations": {"knee_cave": 2},
            "sets_completed": 15,
            "metrics": {"calories": 350},
        })
        assert r.status_code == 201
        assert "session_id" in r.json()

    async def test_metrics_summary(self, auth_client):
        # Submit a session first
        await auth_client.post("/api/v1/sessions/", json={
            "activity": "pushup", "rep_count": 30, "avg_quality": 0.75,
            "sets_completed": 10, "metrics": {"calories": 200},
        })
        r = await auth_client.get("/api/v1/sessions/summary?days=30")
        assert r.status_code == 200
        data = r.json()
        assert data["total_sessions"] >= 1
        assert "activity_breakdown" in data

    async def test_injury_risk_empty(self, auth_client):
        r = await auth_client.get("/api/v1/sessions/injury-risk")
        assert r.status_code == 200
        assert "risks" in r.json()


# ── Gamification tests ────────────────────────────────────────────────────────

class TestGamification:
    async def test_status_initial(self, auth_client):
        r = await auth_client.get("/api/v1/gamification/status")
        assert r.status_code == 200
        data = r.json()
        assert data["points"] == 0
        assert data["streak"] == 0
        assert data["level"] == "Beginner"

    async def test_personal_records_empty(self, auth_client):
        r = await auth_client.get("/api/v1/gamification/personal-records")
        assert r.status_code == 200
        assert r.json()["personal_records"] == []


# ── Health check ──────────────────────────────────────────────────────────────

class TestHealth:
    async def test_health_ok(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
