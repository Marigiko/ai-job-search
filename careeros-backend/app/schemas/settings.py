"""Settings and dashboard schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── SMTP ─────────────────────────────────────────────────────────────────────


class SmtpConfig(BaseModel):
    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    from_name: str = ""
    from_email: str = ""
    reply_to: str | None = None


class SmtpConfigUpdate(BaseModel):
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    use_tls: bool | None = None
    from_name: str | None = None
    from_email: str | None = None
    reply_to: str | None = None


# ── API Keys ─────────────────────────────────────────────────────────────────


class ApiKeys(BaseModel):
    hunter: str = ""
    apollo: str = ""
    serper: str = ""


class ApiKeysUpdate(BaseModel):
    hunter: str | None = None
    apollo: str | None = None
    serper: str | None = None


# ── Outreach Limits ──────────────────────────────────────────────────────────


class OutreachLimits(BaseModel):
    daily_max: int = 50
    hourly_max: int = 10
    delay_seconds: int = 30
    max_per_company: int = 2
    cooldown_hours: int = 72


class OutreachLimitsUpdate(BaseModel):
    daily_max: int | None = None
    hourly_max: int | None = None
    delay_seconds: int | None = None
    max_per_company: int | None = None
    cooldown_hours: int | None = None


# ── Portals ──────────────────────────────────────────────────────────────────


class PortalToggle(BaseModel):
    id: str
    name: str
    enabled: bool
    description: str
    category: str = "aggregator"


# ── A/B Tests ────────────────────────────────────────────────────────────────


class AbTestPerformance(BaseModel):
    template_id: int
    template_name: str
    variant: str
    sent_count: int
    open_rate: float
    reply_rate: float
    is_winner: bool = False


# ── Bundle ───────────────────────────────────────────────────────────────────


class SettingsBundle(BaseModel):
    smtp: SmtpConfig
    api_keys: ApiKeys
    outreach_limits: OutreachLimits
    portals: list[PortalToggle] = Field(default_factory=list)


# ── Dashboard ────────────────────────────────────────────────────────────────


class DashboardSummary(BaseModel):
    active_jobs: int
    applications_this_week: int
    response_rate: float
    total_applications: int


class ActivityPoint(BaseModel):
    date: str
    applications: int
    discoveries: int


class FollowUpItem(BaseModel):
    application_id: int
    job_title: str
    company_name: str | None
    follow_up_date: str
    status: str
    days_overdue: int
