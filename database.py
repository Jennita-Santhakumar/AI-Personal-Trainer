"""
database.py — SQLAlchemy async engine + session factory.
Supports PostgreSQL (Docker) and auto-fallbacks to SQLite (Local Dev).
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import get_settings

settings = get_settings()

db_url = settings.database_url
is_sqlite = "sqlite" in db_url

# If database_url is pointing to postgres hostname outside Docker, use local SQLite fallback
if "postgres:5432" in db_url and not os.environ.get("RUNNING_IN_DOCKER"):
    db_url = "sqlite+aiosqlite:///./fitness_platform.db"
    is_sqlite = True

engine_kwargs = {"echo": settings.debug}
if not is_sqlite:
    engine_kwargs.update({"pool_size": 10, "max_overflow": 20})

engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Create tables only if they don't already exist.
    checkfirst=True prevents crashes when the schema already exists
    (e.g. container restarted with an existing pgdata volume).
    """
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True)
        )
