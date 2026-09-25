"""Pipeline endpoints — Kanban stages, metrics, and application CRUD."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.application import Application
from app.models.company import Company
from app.models.job_posting import JobPosting
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    KanbanItem,
    KanbanResponse,
    PipelineCountsResponse,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.services import pipeline_service

router = APIRouter()


@router.get("/counts", response_model=PipelineCountsResponse)
async def pipeline_counts(
    db: AsyncSession = Depends(get_db),
) -> PipelineCountsResponse:
    """Return the count of applications per pipeline stage."""
    stages = await pipeline_service.stage_counts(db)
    return PipelineCountsResponse(stages=stages)


@router.get("/kanban", response_model=KanbanResponse)
async def kanban_board(
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
) -> KanbanResponse:
    """Return jobs grouped by pipeline stage for the Kanban board."""
    stmt = (
        select(JobPosting, Application)
        .outerjoin(Application, JobPosting.id == Application.job_posting_id)
        .outerjoin(Company, JobPosting.company_id == Company.id)
        .options(selectinload(JobPosting.company))
    )
    if status_filter:
        stmt = stmt.where(Application.status == status_filter)

    rows = (await db.execute(stmt)).all()

    stages: dict[str, list[KanbanItem]] = {s: [] for s in pipeline_service.STAGE_ORDER}
    for job, application in rows:
        item = KanbanItem(
            job_id=job.id,
            job_title=job.title,
            company_name=job.company.name if job.company else None,
            application_id=application.id if application else None,
            status=application.status if application else "discovered",
            applied_date=application.applied_date if application else None,
        )
        stage = item.status if item.status in stages else "discovered"
        stages[stage].append(item)

    return KanbanResponse(stages=stages)


@router.get("/applications", response_model=PaginatedResponse[ApplicationResponse])
async def list_applications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    job_posting_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ApplicationResponse]:
    """List applications with optional filters and pagination."""
    result = await pipeline_service.list_applications(
        db, page, per_page, status_filter, job_posting_id
    )
    return PaginatedResponse[ApplicationResponse](
        data=[ApplicationResponse.model_validate(a) for a in result.items],
        meta=PaginationMeta(page=page, per_page=per_page, total=result.total),
    )


@router.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_application(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Create a new application for a job posting."""
    application = await pipeline_service.create_application(db, payload)
    return ApplicationResponse.model_validate(application)


@router.get("/applications/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Retrieve a single application by ID."""
    application = await pipeline_service.get_application(db, application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    return ApplicationResponse.model_validate(application)


@router.patch("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Partially update an application (e.g., move to a new stage)."""
    application = await pipeline_service.update_application(db, application_id, payload)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    return ApplicationResponse.model_validate(application)


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an application."""
    deleted = await pipeline_service.delete_application(db, application_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
