from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.common import MessageResponse
from app.services import search_service

router = APIRouter()


@router.get("/portals")
async def list_portals() -> list[dict[str, str]]:
    """Return all registered portal plugins with their base URLs."""
    return search_service.list_portals()


@router.get("/health")
async def portal_health() -> dict[str, dict[str, bool] | list[dict[str, str]]]:
    """Run a healthcheck on every registered portal."""
    return {
        "portals": search_service.list_portals(),
        "healthy": await search_service.check_health(),
    }


@router.post("")
async def trigger_search(
    query: str = Query(..., min_length=1, max_length=300, description="Free-text search query"),
    portals: list[str] | None = Query(
        default=None,
        description="Portal names to search. Omit for all registered portals.",
    ),
    location: str | None = Query(default=None, max_length=200),
    remote: bool | None = Query(default=None),
    visa: bool | None = Query(default=None),
    min_salary: int | None = Query(default=None, ge=0),
    jobage: int | None = Query(default=None, ge=0),
    limit: int | None = Query(default=50, ge=1, le=200),
    page: int | None = Query(default=1, ge=1),
    persist: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger a search across configured portals.

    Results are optionally persisted to the job_postings table. The response
    returns task_id, per-portal counts, and total result count.
    """
    result = await search_service.start_search(
        db,
        query,
        portals,
        location=location,
        remote=remote,
        visa=visa,
        min_salary=min_salary,
        jobage=jobage,
        limit=limit or 50,
        page=page or 1,
        persist=persist,
    )
    return result


@router.get("/status/{task_id}")
async def search_status(
    task_id: str | None = None,
) -> dict:
    """Check the status of a search task."""
    return await search_service.get_status(task_id)
