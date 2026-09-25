"""Pipeline stage tracking and application CRUD service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.job_posting import JobPosting
from app.schemas.application import ApplicationCreate, ApplicationUpdate

STAGE_ORDER = [
    "discovered",
    "interested",
    "applied",
    "screening",
    "interview",
    "offer",
    "rejected",
]


@dataclass
class PaginatedResult:
    items: list[Application]
    total: int


async def stage_counts(db: AsyncSession) -> dict[str, int]:
    """Count jobs per pipeline stage."""
    result = await db.execute(
        select(JobPosting.status, func.count()).group_by(JobPosting.status)
    )
    counts: dict[str, int] = {stage: 0 for stage in STAGE_ORDER}
    for status, count in result.all():
        counts[status] = count
    return counts


async def kanban_groups(db: AsyncSession) -> dict[str, list[dict[str, str | int]]]:
    """Group jobs by stage for Kanban display."""
    result = await db.execute(
        select(JobPosting.id, JobPosting.title, JobPosting.status).order_by(
            JobPosting.created_at.desc()
        )
    )
    groups: dict[str, list[dict[str, str | int]]] = {stage: [] for stage in STAGE_ORDER}
    for job_id, title, status in result.all():
        stage = status if status in groups else "discovered"
        groups[stage].append({"id": job_id, "title": title})
    return groups


async def list_applications(
    db: AsyncSession,
    page: int,
    per_page: int,
    status_filter: str | None,
    job_posting_id: int | None,
) -> PaginatedResult:
    """Query applications with optional filters and pagination."""
    query = select(Application)
    count_query = select(func.count()).select_from(Application)

    if status_filter:
        query = query.where(Application.status == status_filter)
        count_query = count_query.where(Application.status == status_filter)
    if job_posting_id is not None:
        query = query.where(Application.job_posting_id == job_posting_id)
        count_query = count_query.where(Application.job_posting_id == job_posting_id)

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Application.created_at.desc())

    items = (await db.execute(query)).scalars().all()
    total = (await db.execute(count_query)).scalar_one()
    return PaginatedResult(items=list(items), total=total)


async def create_application(db: AsyncSession, payload: ApplicationCreate) -> Application:
    """Create a new application."""
    application = Application(**payload.model_dump())
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


async def get_application(db: AsyncSession, application_id: int) -> Application | None:
    """Fetch an application by ID, or None if not found."""
    return await db.get(Application, application_id)


async def update_application(
    db: AsyncSession, application_id: int, payload: ApplicationUpdate
) -> Application | None:
    """Update an existing application, returning None if not found."""
    application = await db.get(Application, application_id)
    if application is None:
        return None

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, key, value)

    await db.commit()
    await db.refresh(application)
    return application


async def delete_application(db: AsyncSession, application_id: int) -> bool:
    """Delete an application. Returns True if deleted."""
    application = await db.get(Application, application_id)
    if application is None:
        return False
    await db.delete(application)
    await db.commit()
    return True
