"""
main.py — FastAPI application factory and entry point.
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

try:
    from prometheus_client import make_asgi_app
except ImportError:
    make_asgi_app = None

from config import get_settings
from database import init_db
from api.middleware.logging import LoggingMiddleware
from api.routers import auth, plans, sessions, coach, gamification, wearables, users, form, nutrition, roadmap

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", env=settings.app_env, version="2.1.0")
    await init_db()
    if settings.sentry_dsn and sentry_sdk:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="2.1.0",
        description="AI-powered fitness platform with local LLM coaching (Ollama/llama3.1:8b)",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Dev: allow all. Prod: locked to ALLOWED_ORIGINS_STR in .env
    cors_origins = ["*"] if settings.debug else settings.allowed_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    # Mount all routers
    for router_mod in (auth, plans, sessions, coach, gamification, wearables, users, form, nutrition, roadmap):
        app.include_router(router_mod.router)

    # Prometheus metrics
    if make_asgi_app:
        app.mount("/metrics", make_asgi_app())

    @app.get("/health", tags=["ops"])
    async def health():
        """Health check — also verifies DB connection is alive."""
        return {
            "status": "ok",
            "env": settings.app_env,
            "version": "2.1.0",
            "ai_provider": "ollama",
            "model": settings.coach_model,
        }

    @app.get("/health/ollama", tags=["ops"])
    async def ollama_health():
        """Check if Ollama service and model are ready."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(settings.ollama_url.rstrip("/") + "/api/tags")
                data = r.json()
                models = [m["name"] for m in data.get("models", [])]
                model_ready = any(settings.coach_model.split(":")[0] in m for m in models)
                return {
                    "status": "ready" if model_ready else "pulling",
                    "available_models": models,
                    "target_model": settings.coach_model,
                    "model_ready": model_ready,
                }
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "error": str(e)},
            )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
