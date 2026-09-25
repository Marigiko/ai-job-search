"""Job posting CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.job_posting import JobPosting
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.job import JobPostingCreate, JobPostingResponse, JobPostingUpdate
from app.services import job_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[JobPostingResponse])
async def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[JobPostingResponse]:
    """List jobs with optional filtering, search, and pagination."""
    result = await job_service.list_jobs(db, page, per_page, status_filter, search)
    return PaginatedResponse[JobPostingResponse](
        data=[JobPostingResponse.model_validate(job) for job in result.items],
        meta=PaginationMeta(page=page, per_page=per_page, total=result.total),
    )


@router.post("", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobPostingCreate,
    db: AsyncSession = Depends(get_db),
) -> JobPostingResponse:
    """Create a new job posting manually."""
    job = await job_service.create_job(db, payload)
    return JobPostingResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobPostingResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> JobPostingResponse:
    """Retrieve a single job posting by ID."""
    job = await db.get(
        JobPosting, job_id, options=[selectinload(JobPosting.company)]
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobPostingResponse.model_validate(job)


@router.patch("/{job_id}", response_model=JobPostingResponse)
async def update_job(
    job_id: int,
    payload: JobPostingUpdate,
    db: AsyncSession = Depends(get_db),
) -> JobPostingResponse:
    """Partially update a job posting."""
    job = await job_service.update_job(db, job_id, payload)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobPostingResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a job posting."""
    deleted = await job_service.delete_job(db, job_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
