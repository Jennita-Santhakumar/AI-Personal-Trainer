"""
config.py — centralised settings via pydantic-settings.

Key fix: pydantic-settings tries to JSON-parse any list[str] field.
We avoid this entirely by using plain str fields for anything
comma-separated, then exposing typed properties.
"""
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "AI Fitness Platform"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me"

    # Use plain str — never list[str] — for env vars that contain commas.
    # pydantic-settings tries json.loads() on list fields and explodes.
    allowed_origins_str: str = "http://localhost:3000,http://localhost:8080"

    # Database
    database_url: str = "postgresql+asyncpg://fitness:fitness@postgres:5432/fitness_platform"
    redis_url: str = "redis://redis:6379/0"

    # InfluxDB
    influx_url: str = "http://influxdb:8086"
    influx_token: str = ""
    influx_org: str = "fitness"
    influx_bucket: str = "metrics"

    # AI Providers & Models
    ollama_url: str = "http://ollama:11434"
    coach_model: str = "llama3.1:8b"
    vector_memory_dir: str = "./coach_memory"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_api_key: str = ""
    ai_provider: str = "auto"   # auto | gemini | groq | ollama

    # Nutrition APIs
    usda_api_key: str = ""   # free at https://fdc.nal.usda.gov/api-guide

    # OAuth
    fitbit_client_id: str = ""
    fitbit_client_secret: str = ""
    google_fit_client_id: str = ""
    google_fit_client_secret: str = ""

    # Storage
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "fitness-platform"

    # Monitoring
    sentry_dsn: str = ""

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def allowed_origins(self) -> list[str]:
        """Split the comma-separated string into a proper list."""
        return [o.strip() for o in self.allowed_origins_str.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
