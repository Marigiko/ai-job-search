"""Analytics endpoints — funnel, outreach, and salary insights."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.analytics import (
    FunnelResponse,
    OutreachAbResponse,
    OutreachMetrics,
    SalaryInsights,
)
from app.services import analytics_service

router = APIRouter()


@router.get("/funnel", response_model=FunnelResponse)
async def funnel_metrics(
    db: AsyncSession = Depends(get_db),
) -> FunnelResponse:
    """Return funnel conversion metrics — stage counts and stage-to-stage rates."""
    return await analytics_service.funnel(db)


@router.get("/outreach", response_model=OutreachMetrics)
async def outreach_metrics(
    db: AsyncSession = Depends(get_db),
) -> OutreachMetrics:
    """Return outreach performance metrics — sent/opened/replied rates."""
    return await analytics_service.outreach_stats(db)


@router.get("/outreach/ab-test", response_model=OutreachAbResponse)
async def outreach_ab_test(
    db: AsyncSession = Depends(get_db),
) -> OutreachAbResponse:
    """Return A/B test results grouped by variant."""
    return await analytics_service.outreach_ab_results(db)


@router.get("/salary", response_model=SalaryInsights)
async def salary_insights(
    db: AsyncSession = Depends(get_db),
) -> SalaryInsights:
    """Return salary distribution insights from tracked postings."""
    return await analytics_service.salary(db)
