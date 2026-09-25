"""Dashboard endpoints — summary stats, activity timeline, follow-ups."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.application import Application
from app.models.job_posting import JobPosting
from app.models.outreach_email import OutreachEmail
from app.schemas.settings import ActivityPoint, DashboardSummary, FollowUpItem

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(db: AsyncSession = Depends(get_db)) -> DashboardSummary:
    """Return high-level dashboard summary stats."""
    # Active jobs = not rejected/withdrawn
    active_result = await db.execute(
        select(func.count()).where(
            JobPosting.status.not_in(("rejected", "withdrawn"))
        )
    )
    active_jobs = active_result.scalar_one()

    # Applications this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    week_result = await db.execute(
        select(func.count()).where(Application.applied_date >= week_ago)
    )
    apps_this_week = week_result.scalar_one()

    # Total applications
    total_result = await db.execute(select(func.count(Application.id)))
    total_apps = total_result.scalar_one()

    # Response rate = applications with status beyond 'applied' / total
    responded_result = await db.execute(
        select(func.count()).where(
            Application.status.in_(
                ("screening", "interview", "offer", "replied")
            )
        )
    )
    responded = responded_result.scalar_one()
    response_rate = round(responded / total_apps, 4) if total_apps > 0 else 0.0

    return DashboardSummary(
        active_jobs=active_jobs,
        applications_this_week=apps_this_week,
        response_rate=response_rate,
        total_applications=total_apps,
    )


@router.get("/activity", response_model=list[ActivityPoint])
async def get_activity(
    days: int = 14,
    db: AsyncSession = Depends(get_db),
) -> list[ActivityPoint]:
    """Return daily application and discovery counts for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Applications per day
    app_result = await db.execute(
        select(
            func.date(Application.applied_date).label("day"),
            func.count().label("count"),
        )
        .where(Application.applied_date >= since)
        .group_by("day")
    )
    apps_by_day = {str(day): count for day, count in app_result.all() if day}

    # Discoveries per day
    disc_result = await db.execute(
        select(
            func.date(JobPosting.discovered_at).label("day"),
            func.count().label("count"),
        )
        .where(JobPosting.discovered_at >= since)
        .group_by("day")
    )
    discs_by_day = {str(day): count for day, count in disc_result.all() if day}

    points: list[ActivityPoint] = []
    for offset in range(days - 1, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=offset)).date()
        day_str = day.isoformat()
        points.append(
            ActivityPoint(
                date=day_str,
                applications=apps_by_day.get(day_str, 0),
                discoveries=discs_by_day.get(day_str, 0),
            )
        )
    return points


@router.get("/follow-ups", response_model=list[FollowUpItem])
async def get_follow_ups(db: AsyncSession = Depends(get_db)) -> list[FollowUpItem]:
    """Return applications that need follow-up."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Find applied applications without recent outreach
    result = await db.execute(
        select(
            Application,
            JobPosting.title,
            JobPosting.company_id,
        )
        .join(JobPosting, Application.job_posting_id == JobPosting.id)
        .where(
            Application.status == "applied",
            Application.applied_date < week_ago,
        )
        .order_by(Application.applied_date.asc())
        .limit(20)
    )

    items: list[FollowUpItem] = []
    for app, title, _company_id in result.all():
        applied = app.applied_date or now
        days_overdue = (now - applied).days - 7
        items.append(
            FollowUpItem(
                application_id=app.id,
                job_title=title,
                company_name=None,
                follow_up_date=(applied + timedelta(days=7)).isoformat(),
                status=app.status,
                days_overdue=max(0, days_overdue),
            )
        )
    return items
