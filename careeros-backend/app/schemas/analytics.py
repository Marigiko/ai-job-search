"""Analytics response schemas — funnel, outreach, and salary metrics."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# --- Funnel ---


class FunnelStage(BaseModel):
    """A single pipeline stage with its count."""

    stage: str
    count: int = Field(ge=0)


class FunnelConversion(BaseModel):
    """Conversion rate between two adjacent pipeline stages."""

    from_stage: str
    to_stage: str
    rate: float = Field(ge=0.0, le=1.0)
    count: int = Field(ge=0)


class FunnelResponse(BaseModel):
    """Full funnel analysis — stage counts and stage-to-stage conversion."""

    model_config = ConfigDict(from_attributes=True)

    total_postings: int = Field(ge=0)
    stages: list[FunnelStage]
    conversions: list[FunnelConversion]


# --- Outreach ---


class OutreachByStatus(BaseModel):
    """Breakdown of emails by status."""

    sent: int = Field(ge=0)
    opened: int = Field(ge=0)
    replied: int = Field(ge=0)
    bounced: int = Field(ge=0)
    failed: int = Field(ge=0)


class OutreachMetrics(BaseModel):
    """Aggregate outreach performance metrics."""

    model_config = ConfigDict(from_attributes=True)

    total_sent: int = Field(ge=0)
    by_status: OutreachByStatus
    open_rate: float = Field(ge=0.0, le=1.0)
    reply_rate: float = Field(ge=0.0, le=1.0)
    bounce_rate: float = Field(ge=0.0, le=1.0)
    avg_time_to_open_hours: float | None = None


class AbTestVariant(BaseModel):
    """A/B test variant performance."""

    variant: str
    sent: int = Field(ge=0)
    open_rate: float = Field(ge=0.0, le=1.0)
    reply_rate: float = Field(ge=0.0, le=1.0)


class OutreachAbResponse(BaseModel):
    """A/B test results across variants."""

    has_data: bool
    variants: list[AbTestVariant]


# --- Salary ---


class SalaryBucket(BaseModel):
    """A salary range bucket with count."""

    range_label: str
    min_bound: int
    max_bound: int
    count: int = Field(ge=0)


class SalaryByCategory(BaseModel):
    """Average salary grouped by a category."""

    category: str
    avg_min: float | None
    avg_max: float | None
    sample_size: int = Field(ge=0)


class SalaryInsights(BaseModel):
    """Comprehensive salary distribution insights."""

    model_config = ConfigDict(from_attributes=True)

    postings_with_salary: int = Field(ge=0)
    avg_salary_min: float | None
    avg_salary_max: float | None
    median_salary_min: int | None
    median_salary_max: int | None
    p25_salary_min: int | None
    p75_salary_max: int | None
    currency: str
    buckets: list[SalaryBucket]
    by_remote_type: list[SalaryByCategory]
