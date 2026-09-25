"""Job posting CRUD service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_posting import JobPosting
from app.schemas.job import JobPostingCreate, JobPostingUpdate


@dataclass
class PaginatedResult:
    items: list[JobPosting]
    total: int


async def list_jobs(
    db: AsyncSession,
    page: int,
    per_page: int,
    status_filter: str | None,
    search: str | None,
) -> PaginatedResult:
    """Query jobs with optional filters and pagination."""
    query = select(JobPosting)
    count_query = select(func.count()).select_from(JobPosting)

    if status_filter:
        query = query.where(JobPosting.status == status_filter)
        count_query = count_query.where(JobPosting.status == status_filter)

    if search:
        term = f"%{search}%"
        query = query.where(
            or_(JobPosting.title.ilike(term), JobPosting.description.ilike(term))
        )
        count_query = count_query.where(
            or_(JobPosting.title.ilike(term), JobPosting.description.ilike(term))
        )

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(JobPosting.created_at.desc())

    items = (await db.execute(query)).scalars().all()
    total = (await db.execute(count_query)).scalar_one()

    return PaginatedResult(items=list(items), total=total)


async def create_job(db: AsyncSession, payload: JobPostingCreate) -> JobPosting:
    """Create a new job posting.

    Serialise with ``mode="json"`` so Pydantic types such as ``HttpUrl``
    become plain strings SQLAlchemy can bind to a ``String`` column.
    """
    job = JobPosting(**payload.model_dump(exclude_unset=True, mode="json"))
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def update_job(
    db: AsyncSession, job_id: int, payload: JobPostingUpdate
) -> JobPosting | None:
    """Update an existing job posting, returning None if not found."""
    job = await db.get(JobPosting, job_id)
    if job is None:
        return None

    for key, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(job, key, value)

    await db.commit()
    await db.refresh(job)
    return job


async def delete_job(db: AsyncSession, job_id: int) -> bool:
    """Delete a job posting. Returns True if deleted."""
    job = await db.get(JobPosting, job_id)
    if job is None:
        return False
    await db.delete(job)
    await db.commit()
    return True
