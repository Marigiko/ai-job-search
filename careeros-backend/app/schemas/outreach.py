"""Outreach email schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.outreach_email import EmailStatus

# ---------------------------------------------------------------------------
# Base / responses
# ---------------------------------------------------------------------------


class OutreachEmailBase(BaseModel):
    recipient_email: EmailStr
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)


class OutreachEmailCreate(OutreachEmailBase):
    application_id: int | None = None
    template_id: int | None = None


class OutreachEmailResponse(OutreachEmailBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int | None = None
    template_id: int | None = None
    status: EmailStatus
    sent_at: datetime | None = None
    opened_at: datetime | None = None
    replied_at: datetime | None = None
    ab_variant: str | None = None


class OutreachQueueItem(BaseModel):
    email_id: int
    recipient: str
    subject: str
    status: str
    queued_at: datetime | None = None


class OutreachSendResult(BaseModel):
    """Result of a send operation."""

    ok: bool
    status: str
    email_id: int | None = None
    error: str | None = None
    rate_info: dict[str, Any] | None = None


class OutreachComposeWithTemplateRequest(BaseModel):
    """Compose an email using a template + variables."""

    recipient_email: EmailStr
    template_id: int
    variables: dict[str, str] = Field(default_factory=dict)
    application_id: int | None = None
    strategy: str = Field(default="best", description="A/B strategy: best, random, round_robin")


class OutreachPreviewRequest(BaseModel):
    """Render a template without saving."""

    template_id: int
    variables: dict[str, str] = Field(default_factory=dict)
    strategy: str = "best"


class OutreachPreviewResponse(BaseModel):
    subject: str
    body: str
    template_id: str
    template_name: str
    ab_variant: str | None = None


class OutreachSendDirectRequest(BaseModel):
    """Compose + send in one call."""

    recipient_email: EmailStr
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    application_id: int | None = None
    template_id: int | None = None
    attachments: list[str] = Field(default_factory=list)
    skip_dedup: bool = False


class OutreachBulkRecipient(BaseModel):
    """A single recipient entry for bulk operations."""

    email: str = Field(min_length=1)
    company: str = ""
    founder_name: str = ""
    trigger: str = ""
    extra: dict[str, str] = Field(default_factory=dict)


class OutreachBulkRequest(BaseModel):
    """Bulk compose + queue/send."""

    template_id: int
    recipients: list[OutreachBulkRecipient] = Field(min_length=1)
    strategy: str = "best"
    mode: str = Field(default="queue", pattern="^(queue|send)$")
    skip_duplicates: bool = True
    attachments: list[str] = Field(default_factory=list)


class OutcomeItem(BaseModel):
    email: str
    status: str  # sent | skipped | rate_limited | error
    reason: str | None = None


class OutreachBulkResponse(BaseModel):
    created: int = 0
    skipped: int = 0
    failed: int = 0
    results: list[OutcomeItem] = Field(default_factory=list)


class OutreachQueueProcessRequest(BaseModel):
    batch_limit: int | None = Field(default=None, ge=1, le=500)
    attachments: list[str] = Field(default_factory=list)


class OutreachStatsResponse(BaseModel):
    counts: dict[str, int] = Field(default_factory=dict)
    total_sent: int = 0
    opened: int = 0
    replied: int = 0
    bounced: int = 0
    failed: int = 0
    queued: int = 0
    draft: int = 0
    open_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0
    sent_today: int = 0
    daily_cap: int = 0


class OutreachFunnelItem(BaseModel):
    stage: str
    count: int
    conversion_pct: float


class OutreachFunnelResponse(BaseModel):
    funnel: list[OutreachFunnelItem]


class TemplateStatsItem(BaseModel):
    id: int
    name: str
    is_ab_test: bool
    ab_variant: str | None = None
    usage_count: int
    reply_rate: float | None = None


class RateLimitStatusResponse(BaseModel):
    allowed: bool
    sent_today: int
    daily_cap: int
    remaining_today: int | None = None
    reason: str | None = None
    retry_after_seconds: int | None = None


class EmailFindRequest(BaseModel):
    domain: str = Field(min_length=1, description="Company domain, e.g. acme.io")
    role: str = Field(default="founder", description="Role to search for")
    verify: bool = Field(default=False, description="Verify via Hunter.io")


class EmailFindResult(BaseModel):
    email: str
    name: str | None = None
    title: str | None = None
    source: str
    confidence: int = 0
    email_valid: bool | None = None


class EmailVerifyRequest(BaseModel):
    email: EmailStr


class EmailVerifyResponse(BaseModel):
    email: str
    valid: bool


class EmailEventResponse(BaseModel):
    event_id: int
    event_type: str
    metadata: dict[str, Any] | None = None
    created_at: datetime


class BounceSyncResponse(BaseModel):
    checked: int = 0
    newly_marked: int = 0


class DedupCheckRequest(BaseModel):
    email: EmailStr


class DedupCheckResponse(BaseModel):
    email: str
    result: str  # ok | already_contacted | bounced
