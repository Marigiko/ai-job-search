"""Portal search service — orchestrates multi-portal job searches."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.search_query import SearchQuery
from app.plugins.base import PortalPlugin
from app.plugins.registry import registry
from app.schemas.job import JobPostingCreate

logger = get_logger(__name__)


def list_portals() -> list[dict[str, str]]:
    """Return metadata for every registered portal plugin."""
    return [
        {"name": plugin.name, "base_url": plugin.base_url}
        for plugin in registry.all()
    ]


def get_portal(name: str) -> PortalPlugin:
    """Return a specific plugin by name, raising ``KeyError`` if unknown."""
    return registry.get(name)


async def start_search(
    db: AsyncSession,
    query: str,
    portals: list[str] | None = None,
    *,
    location: str | None = None,
    remote: bool | None = None,
    visa: bool | None = None,
    min_salary: int | None = None,
    jobage: int | None = None,
    limit: int = 50,
    page: int = 1,
    extra: dict[str, Any] | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Dispatch a search across the requested portals (default: all).

    Args:
        db: Database session used to persist ``SearchQuery`` + results.
        query: Free-text keyword.
        portals: Explicit portal names. ``None`` → every registered plugin.
        persist: When ``True``, upsert discovered jobs into the DB.

    Returns:
        A summary dict with ``task_id``, per-portal ``counts``, and the
        aggregated ``total`` result count.
    """
    task_id = str(uuid.uuid4())
    search = SearchQuery(
        query=query,
        portal=",".join(portals) if portals else "all",
        is_active=True,
    )
    db.add(search)
    await db.commit()

    logger.info(
        "Search started: task=%s query=%s portals=%s",
        task_id,
        query,
        portals or "all",
    )

    results = await registry.search(
        query,
        portals,
        location=location,
        remote=remote,
        visa=visa,
        min_salary=min_salary,
        jobage=jobage,
        limit=limit,
        page=page,
        extra=extra,
    )

    counts: dict[str, int] = {name: len(jobs) for name, jobs in results.items()}
    total = sum(counts.values())

    if persist and total > 0:
        await _persist_results(db, results)
        await db.commit()
        logger.info("Persisted %d job postings from search task=%s", total, task_id)

    return {
        "task_id": task_id,
        "query": query,
        "portals": portals or registry.list_names(),
        "counts": counts,
        "total": total,
    }


async def _persist_results(
    db: AsyncSession,
    results: dict[str, list[JobPostingCreate]],
) -> None:
    """Bulk-upsert job postings, skipping duplicates by URL."""
    from app.services.job_service import create_job

    seen_urls: set[str] = set()
    for portal_name, jobs in results.items():
        for posting in jobs:
            url_str = str(posting.url) if posting.url else None
            if url_str:
                if url_str in seen_urls:
                    continue
                seen_urls.add(url_str)
                # Check if a job with this URL already exists
                from sqlalchemy import select
                from app.models.job_posting import JobPosting
                existing = await db.execute(
                    select(JobPosting.id).where(JobPosting.url == url_str).limit(1)
                )
                if existing.scalar_one_or_none() is not None:
                    continue
            try:
                await create_job(db, posting)
            except Exception:
                logger.warning(
                    "Skipping duplicate job from %s: %s",
                    portal_name,
                    posting.title,
                )
                await db.rollback()


async def get_status(task_id: str | None) -> dict[str, str]:
    """Return search status (placeholder — real status needs task store)."""
    if task_id is None:
        return {"status": "unknown"}
    return {"status": "completed", "task_id": task_id}


async def check_health() -> dict[str, bool]:
    """Run :meth:`PortalPlugin.healthcheck` on every registered plugin."""
    plugins = registry.all()
    results = await asyncio.gather(
        *[plugin.healthcheck() for plugin in plugins],
        return_exceptions=True,
    )
    return {
        plugin.name: bool(ok) if not isinstance(ok, BaseException) else False
        for plugin, ok in zip(plugins, results, strict=True)
    }
