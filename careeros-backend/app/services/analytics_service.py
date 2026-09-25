"""Analytics service — funnel, outreach, and salary metrics."""

from __future__ import annotations

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_posting import JobPosting
from app.models.outreach_email import OutreachEmail
from app.schemas.analytics import (
    AbTestVariant,
    FunnelConversion,
    FunnelResponse,
    FunnelStage,
    OutreachAbResponse,
    OutreachByStatus,
    OutreachMetrics,
    SalaryBucket,
    SalaryByCategory,
    SalaryInsights,
)
from app.services.pipeline_service import STAGE_ORDER

# --- Funnel ---


async def funnel(db: AsyncSession) -> FunnelResponse:
    """Calculate stage counts and stage-to-stage conversion rates."""
    result = await db.execute(
        select(JobPosting.status, func.count()).group_by(JobPosting.status)
    )
    counts: dict[str, int] = {stage: 0 for stage in STAGE_ORDER}
    for status, count in result.all():
        if status in counts:
            counts[status] = count

    total_postings = sum(counts.values())

    stages = [FunnelStage(stage=stage, count=counts[stage]) for stage in STAGE_ORDER]

    conversions: list[FunnelConversion] = []
    for i in range(len(STAGE_ORDER) - 1):
        from_stage = STAGE_ORDER[i]
        to_stage = STAGE_ORDER[i + 1]
        from_count = counts[from_stage]
        to_count = counts[to_stage]
        rate = to_count / from_count if from_count > 0 else 0.0
        conversions.append(
            FunnelConversion(
                from_stage=from_stage,
                to_stage=to_stage,
                rate=round(rate, 4),
                count=to_count,
            )
        )

    return FunnelResponse(
        total_postings=total_postings,
        stages=stages,
        conversions=conversions,
    )


# --- Outreach ---


async def outreach_stats(db: AsyncSession) -> OutreachMetrics:
    """Aggregate outreach email performance metrics."""
    result = await db.execute(
        select(OutreachEmail.status, func.count()).group_by(OutreachEmail.status)
    )
    status_counts: dict[str, int] = {}
    for status, count in result.all():
        status_counts[status] = count

    sent = (
        status_counts.get("sent", 0)
        + status_counts.get("opened", 0)
        + status_counts.get("replied", 0)
    )
    opened = status_counts.get("opened", 0) + status_counts.get("replied", 0)
    replied = status_counts.get("replied", 0)
    bounced = status_counts.get("bounced", 0)
    failed = status_counts.get("failed", 0)
    total_sent = sent + bounced + failed

    open_rate = opened / sent if sent > 0 else 0.0
    reply_rate = replied / sent if sent > 0 else 0.0
    bounce_rate = bounced / total_sent if total_sent > 0 else 0.0

    avg_open_hours = None
    if opened > 0:
        time_result = await db.execute(
            select(
                func.avg(
                    func.strftime("%s", OutreachEmail.opened_at)
                    - func.strftime("%s", OutreachEmail.sent_at)
                )
            ).where(
                OutreachEmail.opened_at.isnot(None),
                OutreachEmail.sent_at.isnot(None),
            )
        )
        avg_seconds = time_result.scalar_one_or_none()
        if avg_seconds is not None:
            avg_open_hours = round(avg_seconds / 3600, 2)

    return OutreachMetrics(
        total_sent=total_sent,
        by_status=OutreachByStatus(
            sent=sent,
            opened=opened,
            replied=replied,
            bounced=bounced,
            failed=failed,
        ),
        open_rate=round(open_rate, 4),
        reply_rate=round(reply_rate, 4),
        bounce_rate=round(bounce_rate, 4),
        avg_time_to_open_hours=avg_open_hours,
    )


async def outreach_ab_results(db: AsyncSession) -> OutreachAbResponse:
    """A/B test results grouped by variant."""
    result = await db.execute(
        select(
            OutreachEmail.ab_variant,
            func.count().label("total"),
            func.sum(
                case(
                    (
                        OutreachEmail.status.in_(("opened", "replied")),
                        1,
                    ),
                    else_=0,
                )
            ).label("opened"),
            func.sum(
                case(
                    (OutreachEmail.status == "replied", 1),
                    else_=0,
                )
            ).label("replied"),
        )
        .where(OutreachEmail.ab_variant.isnot(None))
        .group_by(OutreachEmail.ab_variant)
    )

    rows = result.all()
    if not rows:
        return OutreachAbResponse(has_data=False, variants=[])

    variants: list[AbTestVariant] = []
    for variant, total, opened_count, replied_count in rows:
        if total == 0:
            continue
        variants.append(
            AbTestVariant(
                variant=str(variant),
                sent=total,
                open_rate=round((opened_count or 0) / total, 4),
                reply_rate=round((replied_count or 0) / total, 4),
            )
        )

    return OutreachAbResponse(has_data=bool(variants), variants=variants)


# --- Salary ---


_SALARY_BUCKETS = [
    (0, 30_000, "<30k"),
    (30_000, 50_000, "30-50k"),
    (50_000, 75_000, "50-75k"),
    (75_000, 100_000, "75-100k"),
    (100_000, 130_000, "100-130k"),
    (130_000, 160_000, "130-160k"),
    (160_000, 200_000, "160-200k"),
    (200_000, float("inf"), "200k+"),
]

_DEFAULT_CURRENCY = "USD"


async def salary(db: AsyncSession) -> SalaryInsights:
    """Salary distribution insights with percentiles and histogram."""
    base_query = select(JobPosting).where(
        JobPosting.salary_min.isnot(None),
        JobPosting.salary_max.isnot(None),
    )

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    postings_with_salary = count_result.scalar_one()

    if postings_with_salary == 0:
        return SalaryInsights(
            postings_with_salary=0,
            avg_salary_min=None,
            avg_salary_max=None,
            median_salary_min=None,
            median_salary_max=None,
            p25_salary_min=None,
            p75_salary_max=None,
            currency=_DEFAULT_CURRENCY,
            buckets=[],
            by_remote_type=[],
        )

    agg_result = await db.execute(
        select(
            func.avg(JobPosting.salary_min).label("avg_min"),
            func.avg(JobPosting.salary_max).label("avg_max"),
        ).select_from(base_query.subquery())
    )
    avg_min, avg_max = agg_result.one()

    # Percentiles using sorted offset approach (SQLite compatible)
    median_min = await _percentile_int(db, JobPosting.salary_min, 0.5, base_query)
    median_max = await _percentile_int(db, JobPosting.salary_max, 0.5, base_query)
    p25_min = await _percentile_int(db, JobPosting.salary_min, 0.25, base_query)
    p75_max = await _percentile_int(db, JobPosting.salary_max, 0.75, base_query)

    buckets = await _salary_histogram(db, base_query)
    by_remote = await _salary_by_remote_type(db)

    return SalaryInsights(
        postings_with_salary=postings_with_salary,
        avg_salary_min=round(avg_min, 2) if avg_min else None,
        avg_salary_max=round(avg_max, 2) if avg_max else None,
        median_salary_min=median_min,
        median_salary_max=median_max,
        p25_salary_min=p25_min,
        p75_salary_max=p75_max,
        currency=_DEFAULT_CURRENCY,
        buckets=buckets,
        by_remote_type=by_remote,
    )


async def _percentile_int(
    db: AsyncSession,
    column: object,
    percentile: float,
    base_query,
) -> int | None:
    """Compute an integer percentile for a column within the base query."""
    ordered = select(column).select_from(base_query.subquery()).order_by(column.asc())
    result = await db.execute(ordered)
    values = [row[0] for row in result.all() if row[0] is not None]
    if not values:
        return None
    index = int((len(values) - 1) * percentile)
    return int(values[index])


async def _salary_histogram(db: AsyncSession, base_query) -> list[SalaryBucket]:
    """Build salary range histogram buckets."""
    buckets: list[SalaryBucket] = []
    for low, high, label in _SALARY_BUCKETS:
        bucket_filter = base_query.where(
            JobPosting.salary_min >= low,
            JobPosting.salary_min < high,
        )
        count_result = await db.execute(
            select(func.count()).select_from(bucket_filter.subquery())
        )
        count = count_result.scalar_one()
        buckets.append(
            SalaryBucket(
                range_label=label,
                min_bound=low,
                max_bound=high if high != float("inf") else 999_999,
                count=count,
            )
        )
    return buckets


async def _salary_by_remote_type(db: AsyncSession) -> list[SalaryByCategory]:
    """Average salary grouped by remote work type."""
    result = await db.execute(
        select(
            JobPosting.remote_type,
            func.avg(JobPosting.salary_min).label("avg_min"),
            func.avg(JobPosting.salary_max).label("avg_max"),
            func.count().label("sample"),
        )
        .where(JobPosting.salary_min.isnot(None))
        .group_by(JobPosting.remote_type)
    )

    categories: list[SalaryByCategory] = []
    for remote_type, avg_min, avg_max, sample in result.all():
        categories.append(
            SalaryByCategory(
                category=remote_type or "unspecified",
                avg_min=round(avg_min, 2) if avg_min else None,
                avg_max=round(avg_max, 2) if avg_max else None,
                sample_size=sample,
            )
        )
    return categories
