"""Outreach endpoints — compose, send, queue, and manage emails.

Unified API replacing 8 legacy email scripts. All endpoints are async.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import NotFoundError
from app.schemas.common import MessageResponse
from app.schemas.outreach import (
    BounceSyncResponse,
    DedupCheckRequest,
    DedupCheckResponse,
    EmailEventResponse,
    EmailFindRequest,
    EmailFindResult,
    EmailVerifyRequest,
    EmailVerifyResponse,
    OutcomeItem,
    OutreachBulkRequest,
    OutreachBulkResponse,
    OutreachComposeWithTemplateRequest,
    OutreachEmailCreate,
    OutreachEmailResponse,
    OutreachFunnelItem,
    OutreachFunnelResponse,
    OutreachPreviewRequest,
    OutreachPreviewResponse,
    OutreachQueueItem,
    OutreachQueueProcessRequest,
    OutreachSendDirectRequest,
    OutreachSendResult,
    OutreachStatsResponse,
    RateLimitStatusResponse,
    TemplateStatsItem,
)
from app.services import outreach_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Compose (legacy — preserved)
# ---------------------------------------------------------------------------


@router.post("/compose", response_model=OutreachEmailResponse)
async def compose_email(
    payload: OutreachEmailCreate,
    db: AsyncSession = Depends(get_db),
) -> OutreachEmailResponse:
    """Compose an email (saves as draft)."""
    email = await outreach_service.compose(
        db,
        recipient_email=payload.recipient_email,
        subject=payload.subject,
        body=payload.body,
        application_id=payload.application_id,
        template_id=payload.template_id,
    )
    return OutreachEmailResponse.model_validate(email)


@router.post("/compose/from-template", response_model=OutreachEmailResponse)
async def compose_from_template(
    payload: OutreachComposeWithTemplateRequest,
    db: AsyncSession = Depends(get_db),
) -> OutreachEmailResponse:
    """Compose an email using a template + variables."""
    try:
        email, _tmpl = await outreach_service.compose_from_template(
            db,
            recipient_email=payload.recipient_email,
            template_id=payload.template_id,
            variables=payload.variables,
            application_id=payload.application_id,
            strategy=payload.strategy,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OutreachEmailResponse.model_validate(email)


@router.post("/preview", response_model=OutreachPreviewResponse)
async def preview_email(
    payload: OutreachPreviewRequest,
    db: AsyncSession = Depends(get_db),
) -> OutreachPreviewResponse:
    """Render a template without saving — preview before send."""
    try:
        rendered = await outreach_service.preview_email(
            db,
            template_id=payload.template_id,
            variables=payload.variables,
            strategy=payload.strategy,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OutreachPreviewResponse(**rendered)


# ---------------------------------------------------------------------------
# Send (immediate)
# ---------------------------------------------------------------------------


@router.post("/send", response_model=OutreachSendResult)
async def send_email(
    email_id: int = Query(..., description="Email ID to send"),
    db: AsyncSession = Depends(get_db),
) -> OutreachSendResult:
    """Send a queued/draft email immediately."""
    try:
        result = await outreach_service.send_now(db, email_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if not result["ok"] and result.get("status") == "rate_limited":
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=result,
        )
    return OutreachSendResult(**result)


@router.post("/send/direct", response_model=OutreachSendResult)
async def send_direct(
    payload: OutreachSendDirectRequest,
    db: AsyncSession = Depends(get_db),
) -> OutreachSendResult:
    """Compose + send in one call (bypasses queue)."""
    attachments = [Path(p) for p in payload.attachments if p]
    result = await outreach_service.send_composed(
        db,
        recipient_email=payload.recipient_email,
        subject=payload.subject,
        body=payload.body,
        application_id=payload.application_id,
        template_id=payload.template_id,
        attachments=attachments,
        skip_dedup=payload.skip_dedup,
    )
    return OutreachSendResult(**result)


# ---------------------------------------------------------------------------
# Queue management
# ---------------------------------------------------------------------------


@router.post("/queue", response_model=MessageResponse)
async def queue_email(
    email_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Queue an email for later sending."""
    queued = await outreach_service.enqueue(db, email_id)
    if not queued:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found or not in draft status",
        )
    return MessageResponse(message="queued", detail=str(email_id))


@router.get("/queue", response_model=list[OutreachQueueItem])
async def list_queue(
    db: AsyncSession = Depends(get_db),
) -> list[OutreachQueueItem]:
    """List all queued emails."""
    items = await outreach_service.list_queue(db)
    return [OutreachQueueItem(**item) for item in items]


@router.delete("/queue/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_queue(
    email_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove an email from the queue."""
    removed = await outreach_service.dequeue(db, email_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found or not in queued status",
        )


@router.post("/queue/process", response_model=list[OutreachSendResult])
async def process_queue(
    payload: OutreachQueueProcessRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[OutreachSendResult]:
    """Process queued emails (respects rate limits)."""
    if payload is None:
        payload = OutreachQueueProcessRequest()
    attachments = [Path(p) for p in payload.attachments]
    results = await outreach_service.process_queue(
        db,
        batch_limit=payload.batch_limit,
        attachments=attachments,
    )
    return [OutreachSendResult(**r) for r in results]


# ---------------------------------------------------------------------------
# Bulk operations
# ---------------------------------------------------------------------------


@router.post("/bulk", response_model=OutreachBulkResponse)
async def bulk_outreach(
    payload: OutreachBulkRequest,
    db: AsyncSession = Depends(get_db),
) -> OutreachBulkResponse:
    """Compose + queue or send to multiple recipients."""
    try:
        recipients = [r.model_dump() for r in payload.recipients]
        attachments = [Path(p) for p in payload.attachments]
        if payload.mode == "send":
            results = await outreach_service.send_bulk(
                db,
                template_id=payload.template_id,
                recipients=recipients,
                strategy=payload.strategy,
                attachments=attachments,
            )
            outcome_items = [
                OutcomeItem(
                    email=r["email"],
                    status=r.get("status", "unknown"),
                    reason=r.get("reason") or r.get("error"),
                )
                for r in results
            ]
            return OutreachBulkResponse(
                created=sum(1 for r in results if r.get("ok")),
                skipped=sum(1 for r in results if r.get("status") == "skipped"),
                failed=sum(1 for r in results if r.get("status") in ("error", "failed")),
                results=outcome_items,
            )

        summary = await outreach_service.enqueue_many(
            db,
            template_id=payload.template_id,
            recipients=recipients,
            strategy=payload.strategy,
            skip_duplicates=payload.skip_duplicates,
        )
        return OutreachBulkResponse(**summary)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Events & lifecycle
# ---------------------------------------------------------------------------


@router.post("/{email_id}/events/{event_type}", response_model=EmailEventResponse)
async def record_event(
    email_id: int,
    event_type: str,
    metadata: dict | None = None,
    db: AsyncSession = Depends(get_db),
) -> EmailEventResponse:
    """Record a lifecycle event (opened, replied, bounced, clicked)."""
    allowed = ("opened", "replied", "bounced", "clicked", "unsubscribed")
    if event_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"event_type must be one of {allowed}",
        )
    try:
        event = await outreach_service.record_event(
            db, email_id, event_type, metadata=metadata
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EmailEventResponse(
        event_id=event.id,
        event_type=event.event_type,
        metadata=event.metadata_,
        created_at=event.created_at,
    )


@router.get("/{email_id}/timeline", response_model=list[EmailEventResponse])
async def email_timeline(
    email_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[EmailEventResponse]:
    """Get the event timeline for an email."""
    timeline = await outreach_service.get_email_timeline(db, email_id)
    return [EmailEventResponse(**e) for e in timeline]


# ---------------------------------------------------------------------------
# Dedup & bounce
# ---------------------------------------------------------------------------


@router.post("/dedup-check", response_model=DedupCheckResponse)
async def dedup_check(
    payload: DedupCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> DedupCheckResponse:
    """Check if an email has already been contacted or bounced."""
    result = await outreach_service.dedup_check(db, payload.email)
    return DedupCheckResponse(email=payload.email, result=result.value)


@router.post("/sync-bounces", response_model=BounceSyncResponse)
async def sync_bounces(
    db: AsyncSession = Depends(get_db),
) -> BounceSyncResponse:
    """Check IMAP for bounced emails and mark them in the DB."""
    bounced = await outreach_service.check_bounced_imap()
    newly_marked = await outreach_service.sync_bounces_to_db(db)
    return BounceSyncResponse(checked=len(bounced), newly_marked=newly_marked)


# ---------------------------------------------------------------------------
# Email finder
# ---------------------------------------------------------------------------


@router.post("/find-email", response_model=EmailFindResult)
async def find_email(
    payload: EmailFindRequest,
    db: AsyncSession = Depends(get_db),
) -> EmailFindResult:
    """Find a contact email by domain (Hunter → Apollo → pattern guess)."""
    result = await outreach_service.find_email(
        payload.domain, payload.role, verify=payload.verify
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No email found for {payload.domain}",
        )
    return EmailFindResult(**result)


@router.post("/verify-email", response_model=EmailVerifyResponse)
async def verify_email(
    payload: EmailVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> EmailVerifyResponse:
    """Verify an email address via Hunter.io."""
    valid = await outreach_service.verify_email_hunter(payload.email)
    return EmailVerifyResponse(email=payload.email, valid=valid)


# ---------------------------------------------------------------------------
# Rate limit status
# ---------------------------------------------------------------------------


@router.get("/status/rate-limit", response_model=RateLimitStatusResponse)
async def rate_limit_status(
    db: AsyncSession = Depends(get_db),
) -> RateLimitStatusResponse:
    """Check current rate-limit status."""
    allowed, info = await outreach_service.rate_limit_ok(db)
    return RateLimitStatusResponse(allowed=allowed, **info)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=OutreachStatsResponse)
async def outreach_stats(
    db: AsyncSession = Depends(get_db),
) -> OutreachStatsResponse:
    """Aggregate outreach metrics."""
    stats = await outreach_service.get_outreach_stats(db)
    return OutreachStatsResponse(**stats)


@router.get("/stats/funnel", response_model=OutreachFunnelResponse)
async def outreach_funnel(
    db: AsyncSession = Depends(get_db),
) -> OutreachFunnelResponse:
    """Funnel breakdown: sent → opened → replied."""
    funnel = await outreach_service.get_outreach_funnel(db)
    return OutreachFunnelResponse(
        funnel=[
            OutreachFunnelItem(
                stage=item["stage"],
                count=item["count"],
                conversion_pct=item["conversion_pct"],
            )
            for item in funnel
        ]
    )


@router.get("/stats/templates", response_model=list[TemplateStatsItem])
async def template_stats(
    db: AsyncSession = Depends(get_db),
) -> list[TemplateStatsItem]:
    """Per-template performance stats."""
    stats = await outreach_service.get_template_stats(db)
    return [TemplateStatsItem(**s) for s in stats]


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------


@router.post("/retry/{email_id}", response_model=MessageResponse)
async def retry_failed(
    email_id: int,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Move a failed email back to draft for retry."""
    ok = await outreach_service.retry_failed(db, email_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found or not in failed status",
        )
    return MessageResponse(message="retry_queued", detail=str(email_id))


@router.post("/prune-drafts", response_model=MessageResponse)
async def prune_drafts(
    older_than_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Delete drafts older than N days."""
    count = await outreach_service.prune_old_drafts(db, older_than_days=older_than_days)
    return MessageResponse(message="pruned", detail=str(count))
