"""API v1 root router — aggregates all endpoint modules."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    companies,
    dashboard,
    documents,
    jobs,
    outreach,
    pipeline,
    search,
    settings,
    templates,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(outreach.router, prefix="/outreach", tags=["outreach"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
