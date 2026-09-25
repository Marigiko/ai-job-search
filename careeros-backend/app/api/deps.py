"""FastAPI dependency injection helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for endpoint injection."""
    async for session in get_session():
        yield session
