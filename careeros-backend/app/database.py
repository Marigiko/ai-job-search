"""Async database engine and session management.

Uses aiosqlite under the hood. We set ``journal_mode=MEMORY`` via a connect
pragma because the default rollback journal (DELETE mode) is unreliable in
some sandboxed/containerized environments where the background SQLite worker
thread can stall on filesystem locks after a handful of transactions. MEMORY
mode keeps the journal in RAM — still atomic and crash-safe for a single
connection, and avoids the hang. For a single-user local app this is the
right trade-off; flip to WAL if you ever share the DB file across processes.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_settings = get_settings()


engine: AsyncEngine = create_async_engine(
    _settings.database_url,
    echo=_settings.debug,
    future=True,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    """Apply SQLite pragmas on every new raw connection."""
    try:
        cursor = dbapi_connection.cursor()
        # MEMORY journal avoids the sandbox hang seen with DELETE mode.
        cursor.execute("PRAGMA journal_mode=MEMORY")
        # FK enforcement is off by default in SQLite — turn it on.
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        # Never let a pragma failure break a connect.
        logger.warning("Failed to set SQLite pragmas", exc_info=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session for dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (development convenience — prefer Alembic in production)."""
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def close_db() -> None:
    """Dispose of the engine pool."""
    await engine.dispose()
    logger.info("Database engine disposed")
