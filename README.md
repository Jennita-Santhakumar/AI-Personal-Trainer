# AI Fitness Platform v6

A full-stack AI fitness platform with a **100% local AI coach** powered by [Ollama](https://ollama.ai) + **llama3.1:8b**. No API keys, no cloud costs, no data sent externally.

## Features

- 🤖 **AI Coach** — streaming chat powered by llama3.1:8b via Ollama WebSocket + REST
- 📷 **Pose Detection** — MediaPipe form analysis in-browser
- 🥗 **Nutrition Lookup** — Ollama-powered macro data with curated USDA food database
- 🏋️ **Workout Plans** — AI-generated periodised splits
- 📊 **Dashboard** — session analytics, injury risk scoring, weekly volume charts
- 🏆 **Gamification** — streaks, badges, XP points
- 🧠 **Vector Memory** — ChromaDB-backed semantic recall of past coaching turns
- 📈 **InfluxDB** — time-series metrics for long-term trend tracking
- 🔒 **JWT Auth** — secure user accounts with bcrypt password hashing
- ⚙️ **Celery** — background jobs (daily briefings, weekly reviews)

## Quick Start

```bash
# 1. Clone / extract the project
cd ai-fitness-platform-v6

# 2. Start everything (first run downloads llama3.1:8b — ~4.7GB, takes 5-15 min)
docker compose up --build

# 3. Open the app
open http://localhost:3000

# Demo account: demo@fitnessplatform.com / Demo1234!
```

> **First-run note:** The `ollama-pull` service downloads llama3.1:8b on first start.
> Track progress: `docker compose logs -f ollama-pull`
> After the model is cached in the `fitness_ollama_models` Docker volume, restarts are instant.

## Services

| Service   | URL                          | Description                    |
|-----------|------------------------------|--------------------------------|
| Frontend  | http://localhost:3000        | React app (nginx)              |
| API       | http://localhost:8100/docs   | FastAPI + Swagger UI           |
| Ollama    | http://localhost:11434       | Local LLM server               |
| Postgres  | localhost:5499               | Main database                  |
| Redis     | localhost:6399               | Cache + Celery broker          |
| InfluxDB  | http://localhost:8187        | Time-series metrics            |
| RustFS    | http://localhost:9101        | Local S3-compatible storage UI |

## Environment Variables (.env)

All defaults are pre-configured and work out of the box. Key settings:

| Variable           | Default                              | Description                        |
|--------------------|--------------------------------------|------------------------------------|
| `OLLAMA_URL`       | `http://ollama:11434`                | Ollama service URL                 |
| `COACH_MODEL`      | `llama3.1:8b`                        | LLM model to use                   |
| `DATABASE_URL`     | postgres @ `postgres:5432`           | Async SQLAlchemy URL               |
| `REDIS_URL`        | redis @ `redis:6379`                 | Celery broker + result backend     |
| `SECRET_KEY`       | `change-me-in-production-...`        | JWT signing key — change in prod!  |
| `VECTOR_MEMORY_DIR`| `/app/coach_memory`                  | ChromaDB persistence path          |

## Project Structure

```
ai-fitness-platform-v6/
├── api/
│   ├── middleware/     auth.py, logging.py
│   └── routers/        auth, plans, sessions, coach, gamification,
│                       wearables, users, form, nutrition
├── features/
│   ├── coach/          AICoach, VectorMemoryStore (ChromaDB), prompts
│   ├── gamification/   GamificationEngine, badges, InjuryRiskAnalyzer
│   ├── metrics/        RunMetricsTracker
│   └── workout_split/  AI plan generator (Ollama)
├── frontend/
│   └── src/
│       ├── components/ Dashboard, CoachChat, PlanGenerator, BadgeGrid
│       ├── pages/      Form, Pose, Nutrition, Profile, Plan, Badges
│       ├── hooks/      useCoach (WS streaming with HTTP fallback)
│       └── services/   api.js (all REST + WS calls)
├── ml/                 InjuryRiskModel (scikit-learn)
├── migrations/         Alembic async migrations
├── docker/             Dockerfile.api, postgres-init/
├── scripts/            seed_db.py
├── docker-compose.yml
├── .env
└── requirements.txt
```

## Switching the LLM Model

Change `COACH_MODEL` in `.env` and update the pull command in `docker-compose.yml`:

```bash
# Example: use mistral instead of llama3.1:8b
COACH_MODEL=mistral:7b
# In docker-compose.yml ollama-pull entrypoint:
# "ollama pull mistral:7b"
```

Any model on [Ollama's library](https://ollama.ai/library) works.

## Health Checks

```bash
curl http://localhost:8100/health           # API status
curl http://localhost:8100/health/ollama    # Ollama + model status
```

## Known Issues & Fixes (v6 vs v5)

1. **Hardcoded `llama3.1:8b` model name** — now reads from `settings.coach_model`
2. **New `httpx.AsyncClient` per coach request** — replaced with a shared connection-pooled client
3. **Stale Gemini/API-key UI banners** — all replaced with Ollama-specific status messages
4. **`migrate` service had no dependency ordering** — `api` now waits for `service_completed_successfully`
5. **No demo user on fresh start** — added `seed` service that calls `/api/v1/auth/register`
6. **`bcrypt==4.0.1` conflict with passlib** — pinned to `bcrypt==4.1.3`
7. **`chromadb==0.5.0` instability** — pinned to `0.4.24`
8. **Ollama healthcheck used `ollama list`** (slow/unreliable) — changed to `curl` against REST API
9. **nginx missing gzip + static caching** — added for better frontend performance
10. **`ALLOWED_ORIGINS_STR`** didn't include port 3100 — fixed
11. **`/health/ollama` endpoint added** — shows model readiness status
