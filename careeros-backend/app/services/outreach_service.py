"""Outreach service — unified email composition, sending, and queue management.

Consolidates the 8 legacy email scripts into a single async module:

* SMTP sending            (outreach_sender.py, send_unified.py, send_all_applications.py, …)
* Deduplication           (dedup.py, send_unified.py)
* A/B template selection  (ab_templates.py)
* Bounce tracking         (check_bounced_emails.py)
* Rate limiting           (outreach_sender.py --max-per-day / --delay-min)
* Queue management        (inline in every sender)
* Email finding           (email_finder.py — Hunter / Apollo / pattern guessing)

All functions are async and run inside the FastAPI event loop. The stdlib
``smlib`` call is wrapped in :func:`asyncio.to_thread` so it never blocks.
"""

from __future__ import annotations

import asyncio
import random
import re
import smtplib
import ssl
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.models.email_event import EmailEvent
from app.models.email_template import EmailTemplate
from app.models.outreach_email import EmailStatus, OutreachEmail

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal types
# ---------------------------------------------------------------------------

class DedupResult(Enum):
    """Outcome of a dedup check."""

    OK = "ok"
    ALREADY_CONTACTED = "already_contacted"
    BOUNCED = "bounced"


class AbsStrategy(str, Enum):
    """A/B template selection strategy."""

    BEST = "best"
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"


# ---------------------------------------------------------------------------
# SMTP transport
# ---------------------------------------------------------------------------


async def send_email_smtp(
    recipient: str,
    subject: str,
    body: str,
    *,
    attachments: list[Path] | None = None,
    sender_override: str | None = None,
) -> dict[str, Any]:
    """Send a single email via SMTP (async wrapper around stdlib).

    Returns a dict with ``ok`` (bool) and ``error`` (str | None).
    Does **not** touch the DB — callers record the ``OutreachEmail`` row.
    """
    settings = get_settings()
    sender = sender_override or settings.smtp_sender
    password = settings.smtp_password

    if not sender or not password:
        return {
            "ok": False,
            "error": "SMTP credentials not configured (smtp_sender / smtp_password)",
        }

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    for path in attachments or []:
        if not path.exists():
            logger.warning("Attachment not found, skipping: %s", path)
            continue
        with open(path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={path.name}")
        msg.attach(part)

    def _sync_send() -> None:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
            server.login(sender, password)
            server.send_message(msg)

    try:
        await asyncio.to_thread(_sync_send)
        logger.info("Email sent to %s — subject: %.60s", recipient, subject)
        return {"ok": True, "error": None}
    except smtplib.SMTPAuthenticationError as exc:
        logger.error("SMTP auth failed: %s", exc)
        return {"ok": False, "error": "SMTP authentication failed"}
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending to %s: %s", recipient, exc)
        return {"ok": False, "error": f"SMTP error: {exc}"}
    except Exception as exc:
        logger.exception("Unexpected error sending email to %s", recipient)
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


async def dedup_check(db: AsyncSession, email: str) -> DedupResult:
    """Check whether ``email`` may be contacted.

    Looks up the ``outreach_emails`` table — any row with status ``sent``,
    ``queued`` or ``opened`` counts as already-contacted. A row with status
    ``bounced`` counts as bounced.
    """
    normalized = email.lower().strip()
    result = await db.execute(
        select(OutreachEmail.status).where(
            func.lower(OutreachEmail.recipient_email) == normalized,
        )
    )
    statuses = [row for row in result.scalars().all()]

    if not statuses:
        return DedupResult.OK
    if "bounced" in statuses:
        return DedupResult.BOUNCED
    return DedupResult.ALREADY_CONTACTED


async def is_contacted(db: AsyncSession, email: str) -> bool:
    """True if ``email`` was ever sent/queued/opened."""
    return (await dedup_check(db, email)) is not DedupResult.BOUNCED


async def is_bounced(db: AsyncSession, email: str) -> bool:
    """True if ``email`` has a bounced record."""
    return (await dedup_check(db, email)) is DedupResult.BOUNCED


async def get_contacted_count(db: AsyncSession) -> int:
    """Count distinct contacted recipient emails."""
    result = await db.execute(
        select(func.count(func.distinct(func.lower(OutreachEmail.recipient_email)))).where(
            OutreachEmail.status.in_(["sent", "queued", "opened", "replied"])
        )
    )
    return int(result.scalar_one() or 0)


async def get_bounced_emails(db: AsyncSession) -> list[dict[str, Any]]:
    """Return list of bounced emails with their last sent_at."""
    result = await db.execute(
        select(
            OutreachEmail.recipient_email,
            func.max(OutreachEmail.sent_at),
        )
        .where(OutreachEmail.status == "bounced")
        .group_by(OutreachEmail.recipient_email)
    )
    return [
        {"email": email, "sent_at": sent_at}
        for email, sent_at in result.all()
    ]


# ---------------------------------------------------------------------------
# A/B template selection
# ---------------------------------------------------------------------------


async def select_ab_template(
    db: AsyncSession,
    strategy: AbsStrategy | str = AbsStrategy.BEST,
) -> tuple[EmailTemplate | None, str | None]:
    """Choose a template by strategy. Returns ``(template, variant)``.

    * ``best``        — highest ``reply_rate`` (min 3 uses), else random.
    * ``random``      — uniform random across all templates.
    * ``round_robin`` — least recently used.
    """
    if isinstance(strategy, str):
        strategy = AbsStrategy(strategy)

    result = await db.execute(
        select(EmailTemplate).order_by(EmailTemplate.name)
    )
    templates = list(result.scalars().all())

    if not templates:
        return None, None

    if len(templates) == 1:
        return templates[0], templates[0].ab_variant

    if strategy is AbsStrategy.RANDOM:
        chosen = random.choice(templates)
        return chosen, chosen.ab_variant

    if strategy is AbsStrategy.BEST:
        # Pick highest reply_rate with min 3 uses.
        eligible = [t for t in templates if (t.usage_count or 0) >= 3 and t.reply_rate is not None]
        if eligible:
            chosen = max(eligible, key=lambda t: t.reply_rate or 0.0)
            return chosen, chosen.ab_variant
        chosen = random.choice(templates)
        return chosen, chosen.ab_variant

    # round_robin: least recently used (lowest usage_count).
    chosen = min(templates, key=lambda t: t.usage_count or 0)
    return chosen, chosen.ab_variant


async def render_template(
    template: EmailTemplate,
    variables: dict[str, str],
) -> tuple[str, str]:
    """Render ``subject`` and ``body`` with ``variables`` using ``str.format``.

    Unknown keys are left intact so partial renders don't crash.
    """
    safe_vars = {k: v for k, v in variables.items() if v is not None}

    def _render(text: str) -> str:
        try:
            return text.format_map(_SafeDict(safe_vars))
        except (KeyError, IndexError):
            return text

    return _render(template.subject_template), _render(template.body_template)


class _SafeDict(dict):
    """Dict that returns ``{key}`` for missing keys instead of raising."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


async def record_template_usage(
    db: AsyncSession,
    template_id: int,
    *,
    replied: bool = False,
) -> None:
    """Increment ``usage_count`` and update rolling ``reply_rate``."""
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        return

    current_count = template.usage_count or 0
    current_rate = template.reply_rate or 0.0

    new_count = current_count + 1
    # Rolling average: new_rate = old_rate + (observation - old_rate) / n
    observation = 1.0 if replied else 0.0
    new_rate = current_rate + (observation - current_rate) / new_count

    template.usage_count = new_count
    template.reply_rate = round(new_rate, 4)
    await db.commit()


async def get_template_stats(db: AsyncSession) -> list[dict[str, Any]]:
    """Return per-template performance stats."""
    result = await db.execute(
        select(
            EmailTemplate.id,
            EmailTemplate.name,
            EmailTemplate.is_ab_test,
            EmailTemplate.ab_variant,
            EmailTemplate.usage_count,
            EmailTemplate.reply_rate,
        ).order_by(EmailTemplate.reply_rate.nulls_last())
    )
    return [
        {
            "id": tid,
            "name": name,
            "is_ab_test": is_ab,
            "ab_variant": variant,
            "usage_count": usage,
            "reply_rate": rate,
        }
        for tid, name, is_ab, variant, usage, rate in result.all()
    ]


# ---------------------------------------------------------------------------
# Compose
# ---------------------------------------------------------------------------


async def compose(
    db: AsyncSession,
    *,
    recipient_email: str,
    subject: str,
    body: str,
    application_id: int | None = None,
    template_id: int | None = None,
    ab_variant: str | None = None,
) -> OutreachEmail:
    """Save a new email as ``draft``."""
    email = OutreachEmail(
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        application_id=application_id,
        template_id=template_id,
        ab_variant=ab_variant,
        status="draft",
    )
    db.add(email)
    await db.commit()
    await db.refresh(email)
    return email


async def compose_from_template(
    db: AsyncSession,
    *,
    recipient_email: str,
    template_id: int,
    variables: dict[str, str],
    application_id: int | None = None,
    strategy: AbsStrategy | str = AbsStrategy.BEST,
) -> tuple[OutreachEmail, EmailTemplate]:
    """Compose an email using a template. If ``template_id`` points to an A/B
    template, the service picks the variant per ``strategy``."""
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError(f"Template {template_id} not found")

    # If the template is part of an A/B test, select the variant.
    chosen = template
    if template.is_ab_test:
        chosen, _variant = await select_ab_template(db, strategy)
        if chosen is None:
            chosen = template

    subject, body = await render_template(chosen, variables)
    email = await compose(
        db,
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        application_id=application_id,
        template_id=chosen.id,
        ab_variant=chosen.ab_variant,
    )
    return email, chosen


async def preview_email(
    db: AsyncSession,
    *,
    template_id: int,
    variables: dict[str, str],
    strategy: AbsStrategy | str = AbsStrategy.BEST,
) -> dict[str, str]:
    """Render a template without saving — used for preview-before-send."""
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError(f"Template {template_id} not found")

    chosen = template
    if template.is_ab_test:
        chosen, _variant = await select_ab_template(db, strategy)
        if chosen is None:
            chosen = template

    subject, body = await render_template(chosen, variables)
    return {
        "subject": subject,
        "body": body,
        "template_id": str(chosen.id),
        "template_name": chosen.name,
        "ab_variant": chosen.ab_variant,
    }


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


async def count_sent_today(db: AsyncSession) -> int:
    """Count emails sent since UTC midnight."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    result = await db.execute(
        select(func.count(OutreachEmail.id)).where(
            OutreachEmail.status == "sent",
            OutreachEmail.sent_at >= today_start,
        )
    )
    return int(result.scalar_one() or 0)


async def rate_limit_ok(db: AsyncSession) -> tuple[bool, dict[str, Any]]:
    """Check daily cap and minimum interval.

    Returns ``(allowed, info)`` where ``info`` carries the current usage.
    """
    settings = get_settings()
    sent_today = await count_sent_today(db)
    cap = settings.outreach_daily_cap

    info: dict[str, Any] = {
        "sent_today": sent_today,
        "daily_cap": cap,
        "remaining_today": max(0, cap - sent_today) if cap else None,
    }

    if cap and sent_today >= cap:
        info["reason"] = f"Daily cap reached ({cap})"
        return False, info

    # Check interval since last send.
    result = await db.execute(
        select(OutreachEmail.sent_at)
        .where(OutreachEmail.status == "sent")
        .order_by(OutreachEmail.sent_at.desc())
        .limit(1)
    )
    last_sent: datetime | None = result.scalar_one_or_none()
    if last_sent is not None:
        elapsed = (datetime.now(timezone.utc) - last_sent).total_seconds()
        if elapsed < settings.outreach_min_interval_seconds:
            wait = int(settings.outreach_min_interval_seconds - elapsed)
            info["reason"] = f"Rate limit: wait {wait}s"
            info["retry_after_seconds"] = wait
            return False, info

    return True, info


# ---------------------------------------------------------------------------
# Send (immediate)
# ---------------------------------------------------------------------------


async def send_now(
    db: AsyncSession,
    email_id: int,
    *,
    skip_dedup: bool = False,
    attachments: list[Path] | None = None,
) -> dict[str, Any]:
    """Send a draft/queued email immediately.

    Runs dedup + rate-limit checks, dispatches via SMTP, records status.
    Returns a result dict with ``ok``, ``status``, and optional ``error``.
    """
    email = await db.get(OutreachEmail, email_id)
    if email is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError(f"Email {email_id} not found")

    if email.status not in ("draft", "queued"):
        return {
            "ok": False,
            "status": email.status,
            "error": f"Cannot send email in status '{email.status}'",
        }

    # Dedup check.
    if not skip_dedup:
        dedup = await dedup_check(db, email.recipient_email)
        if dedup is DedupResult.BOUNCED:
            email.status = "bounced"
            await db.commit()
            return {
                "ok": False,
                "status": "bounced",
                "error": f"{email.recipient_email} previously bounced",
            }
        if dedup is DedupResult.ALREADY_CONTACTED:
            return {
                "ok": False,
                "status": "duplicate",
                "error": f"{email.recipient_email} already contacted",
            }

    # Rate limit check.
    allowed, info = await rate_limit_ok(db)
    if not allowed:
        return {
            "ok": False,
            "status": "rate_limited",
            "error": info.get("reason"),
            "rate_info": info,
        }

    # Send.
    result = await send_email_smtp(
        email.recipient_email,
        email.subject,
        email.body,
        attachments=attachments,
    )

    now = datetime.now(timezone.utc)
    if result["ok"]:
        email.status = "sent"
        email.sent_at = now
        await db.commit()

        if email.template_id:
            await record_template_usage(db, email.template_id)

        await _record_event(db, email.id, "sent")
        await db.commit()
        return {"ok": True, "status": "sent", "email_id": email.id}

    email.status = "failed"
    await db.commit()
    await _record_event(db, email.id, "failed", metadata={"error": result["error"]})
    await db.commit()
    return {"ok": False, "status": "failed", "error": result["error"]}


async def send_composed(
    db: AsyncSession,
    *,
    recipient_email: str,
    subject: str,
    body: str,
    application_id: int | None = None,
    template_id: int | None = None,
    attachments: list[Path] | None = None,
    skip_dedup: bool = False,
) -> dict[str, Any]:
    """Compose + send in one call."""
    email = await compose(
        db,
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        application_id=application_id,
        template_id=template_id,
    )
    return await send_now(db, email.id, skip_dedup=skip_dedup, attachments=attachments)


# ---------------------------------------------------------------------------
# Queue management
# ---------------------------------------------------------------------------


async def enqueue(db: AsyncSession, email_id: int) -> bool:
    """Move a draft email to ``queued``."""
    email = await db.get(OutreachEmail, email_id)
    if email is None or email.status != "draft":
        return False
    email.status = "queued"
    await db.commit()
    await _record_event(db, email.id, "queued")
    await db.commit()
    return True


async def dequeue(db: AsyncSession, email_id: int) -> bool:
    """Remove an email from the queue back to draft."""
    email = await db.get(OutreachEmail, email_id)
    if email is None or email.status != "queued":
        return False
    email.status = "draft"
    await db.commit()
    return True


async def list_queue(
    db: AsyncSession,
    *,
    status_filter: EmailStatus | None = "queued",
) -> list[dict[str, Any]]:
    """List queued (or filtered) emails."""
    stmt = select(
        OutreachEmail.id,
        OutreachEmail.recipient_email,
        OutreachEmail.subject,
        OutreachEmail.status,
        OutreachEmail.created_at,
    )
    if status_filter:
        stmt = stmt.where(OutreachEmail.status == status_filter)
    stmt = stmt.order_by(OutreachEmail.created_at.asc())
    result = await db.execute(stmt)
    return [
        {
            "email_id": row.id,
            "recipient": row.recipient_email,
            "subject": row.subject,
            "status": row.status,
            "queued_at": row.created_at,
        }
        for row in result.all()
    ]


async def process_queue(
    db: AsyncSession,
    *,
    batch_limit: int | None = None,
    attachments: list[Path] | None = None,
) -> list[dict[str, Any]]:
    """Process queued emails up to ``batch_limit`` (None = all).

    Respects rate limits — stops when the daily cap is hit or the minimum
    interval has not elapsed.
    """
    settings = get_settings()
    queued = await list_queue(db, status_filter="queued")
    results: list[dict[str, Any]] = []

    for email_info in queued:
        # Re-check rate limit before each send.
        allowed, info = await rate_limit_ok(db)
        if not allowed:
            results.append({
                "email_id": email_info["email_id"],
                "status": "rate_limited",
                "error": info.get("reason"),
            })
            break

        result = await send_now(db, email_info["email_id"], attachments=attachments)
        results.append({"email_id": email_info["email_id"], **result})

        if result.get("ok") and settings.outreach_min_interval_seconds:
            await asyncio.sleep(settings.outreach_min_interval_seconds)

        if batch_limit and len([r for r in results if r.get("status") == "sent"]) >= batch_limit:
            break

    return results


async def clear_failed(db: AsyncSession) -> int:
    """Delete all emails in ``failed`` status. Returns count deleted."""
    result = await db.execute(select(OutreachEmail).where(OutreachEmail.status == "failed"))
    failed = list(result.scalars().all())
    for email in failed:
        await db.delete(email)
    await db.commit()
    return len(failed)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


async def _record_event(
    db: AsyncSession,
    email_id: int,
    event_type: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> EmailEvent:
    """Append an event to an email's timeline."""
    event = EmailEvent(
        outreach_email_id=email_id,
        event_type=event_type,
        metadata_=metadata,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    return event


async def record_event(
    db: AsyncSession,
    email_id: int,
    event_type: Literal["opened", "replied", "bounced", "clicked", "unsubscribed"],
    *,
    metadata: dict[str, Any] | None = None,
) -> EmailEvent:
    """Record a lifecycle event and update the email's status accordingly."""
    email = await db.get(OutreachEmail, email_id)
    if email is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError(f"Email {email_id} not found")

    now = datetime.now(timezone.utc)
    if event_type == "opened" and email.opened_at is None:
        email.opened_at = now
        email.status = "opened"
    elif event_type == "replied":
        email.replied_at = now
        email.status = "replied"
        if email.template_id:
            await record_template_usage(db, email.template_id, replied=True)
    elif event_type == "bounced":
        email.status = "bounced"
    elif event_type == "clicked":
        pass  # metadata-only

    event = await _record_event(db, email_id, event_type, metadata=metadata)
    await db.commit()
    await db.refresh(email)
    return event


async def get_email_timeline(
    db: AsyncSession, email_id: int
) -> list[dict[str, Any]]:
    """Return events for an email, oldest first."""
    result = await db.execute(
        select(EmailEvent)
        .where(EmailEvent.outreach_email_id == email_id)
        .order_by(EmailEvent.created_at.asc())
    )
    return [
        {
            "event_id": e.id,
            "event_type": e.event_type,
            "metadata": e.metadata_,
            "created_at": e.created_at,
        }
        for e in result.scalars().all()
    ]


# ---------------------------------------------------------------------------
# Email finder — Hunter / Apollo / pattern guessing
# ---------------------------------------------------------------------------


async def find_email_hunter(
    domain: str,
    role: str = "founder",
) -> dict[str, Any] | None:
    """Search Hunter.io for an email by domain."""
    settings = get_settings()
    if not settings.hunter_api_key:
        return None
    url = (
        "https://api.hunter.io/v2/domain-search"
        f"?domain={domain}&api_key={settings.hunter_api_key}"
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json().get("data", {})
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Hunter.io error for %s: %s", domain, exc)
        return None

    emails = data.get("emails", [])
    if not emails:
        return None

    role_lower = role.lower()
    for entry in emails:
        position = (entry.get("position") or "").lower()
        first = (entry.get("first_name") or "").lower()
        if role_lower in position or role_lower in first or any(
            r in position for r in ("founder", "ceo", "cto", "co-founder")
        ):
            return {
                "email": entry["value"],
                "name": f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip(),
                "title": entry.get("position", ""),
                "source": "hunter",
                "confidence": entry.get("confidence", 0),
            }

    entry = emails[0]
    return {
        "email": entry["value"],
        "name": f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip(),
        "title": entry.get("position", ""),
        "source": "hunter",
        "confidence": entry.get("confidence", 0),
    }


async def find_email_apollo(
    domain: str,
    role: str = "founder",
) -> dict[str, Any] | None:
    """Search Apollo.io for a contact email by domain."""
    settings = get_settings()
    if not settings.apollo_api_key:
        return None
    url = "https://api.apollo.io/v1/mixed_people/search"
    payload = {
        "q_organization_domains": [domain],
        "person_titles": [role, "founder", "ceo", "cto", "co-founder"],
        "per_page": 5,
    }
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": settings.apollo_api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            people = resp.json().get("people", [])
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Apollo.io error for %s: %s", domain, exc)
        return None

    for person in people:
        email = person.get("email")
        if email:
            return {
                "email": email if isinstance(email, str) else email[0],
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "title": person.get("title", ""),
                "source": "apollo",
                "confidence": 80,
            }
    return None


def guess_email_pattern(domain: str, name: str | None = None) -> dict[str, Any]:
    """Guess an email from common patterns (low accuracy, free)."""
    patterns = [f"founder@{domain}", f"hello@{domain}", f"team@{domain}", f"hi@{domain}"]
    if name:
        clean = name.lower().strip()
        parts = clean.split()
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) > 1 else ""
        patterns.extend([
            f"{first}@{domain}",
            f"{first}.{last}@{domain}",
            f"{first[0]}{last}@{domain}" if first and last else f"{first}@{domain}",
        ])
    return {
        "email": patterns[0],
        "name": name or "",
        "title": "unknown",
        "source": "pattern-guess",
        "confidence": 10,
    }


async def verify_email_hunter(email: str) -> bool:
    """Verify an email via Hunter.io."""
    settings = get_settings()
    if not settings.hunter_api_key:
        return False
    url = (
        "https://api.hunter.io/v2/email-verifier"
        f"?email={email}&api_key={settings.hunter_api_key}"
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            status = resp.json().get("data", {}).get("status", "")
    except (httpx.HTTPError, ValueError):
        return False
    return status in ("valid", "accept_all", "webmail")


async def find_email(
    domain: str,
    role: str = "founder",
    *,
    verify: bool = False,
) -> dict[str, Any] | None:
    """Find the best email for a role at a company domain.

    Tries: Hunter → Apollo → pattern guessing. Optionally verifies via Hunter.
    """
    result = await find_email_hunter(domain, role)
    if result and (result.get("confidence", 0) >= 70):
        if verify:
            result["email_valid"] = await verify_email_hunter(result["email"])
        return result

    apollo = await find_email_apollo(domain, role)
    if apollo:
        if verify and get_settings().hunter_api_key:
            apollo["email_valid"] = await verify_email_hunter(apollo["email"])
        return apollo

    guess = guess_email_pattern(domain)
    if verify:
        guess["email_valid"] = False
    return guess


# ---------------------------------------------------------------------------
# Bounce checking (IMAP)
# ---------------------------------------------------------------------------


BOUNCE_PATTERNS = [
    r"Final-Recipient:[^<]*<([^>]+)>",
    r"Original-Recipient:[^<]*<([^>]+)>",
    r"failed\s+permanently[^<]*<([^>]+)>",
    r"Delivery\s+to\s+the\s+following\s+recipient\s+failed[^<]*<([^>]+)>",
    r"action:\s*failed[^<]*<([^>]+)>",
]


def _extract_bounced_email(body: str) -> str | None:
    """Extract the bounced recipient from a DSN body."""
    for pattern in BOUNCE_PATTERNS:
        match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).lower()
    return None


async def check_bounced_imap() -> list[dict[str, Any]]:
    """Connect to Gmail via IMAP and collect bounced emails.

    Returns a list of ``{"bounced_email": ...}`` dicts. Requires
    ``smtp_sender`` + ``smtp_password`` to be configured.
    """
    settings = get_settings()
    if not settings.smtp_password or not settings.smtp_sender:
        return []

    import imaplib

    bounced: list[dict[str, Any]] = []

    def _sync_check() -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        try:
            mail.login(settings.smtp_sender, settings.smtp_password)
            for folder in ("INBOX", "[Gmail]/Trash", "[Gmail]/Papelera"):
                try:
                    mail.select(folder)
                except Exception:
                    continue
                _, messages = mail.search(
                    None, '(SUBJECT "Delivery Status Notification")'
                )
                if messages[0]:
                    for msg_id in messages[0].split():
                        _, msg_data = mail.fetch(msg_id, "(RFC822)")
                        raw = msg_data[0][1]
                        import email as email_mod

                        msg = email_mod.message_from_bytes(raw)
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    charset = part.get_content_charset() or "utf-8"
                                    body = part.get_payload(decode=True).decode(
                                        charset, errors="replace"
                                    )
                                    break
                        else:
                            charset = msg.get_content_charset() or "utf-8"
                            body = msg.get_payload(decode=True).decode(
                                charset, errors="replace"
                            )
                        recipient = _extract_bounced_email(body)
                        if recipient:
                            found.append(
                                {
                                    "bounced_email": recipient,
                                    "folder": folder,
                                }
                            )
        finally:
            with suppress(Exception):
                mail.logout()
        return found

    bounced = await asyncio.to_thread(_sync_check)
    return bounced


async def sync_bounces_to_db(db: AsyncSession) -> int:
    """Run IMAP bounce check and mark matching emails as ``bounced``.

    Returns the number of newly-marked bounces.
    """
    bounced = await check_bounced_imap()
    if not bounced:
        return 0

    marked = 0
    seen: set[str] = set()
    for entry in bounced:
        email = entry["bounced_email"]
        if email in seen:
            continue
        seen.add(email)

        result = await db.execute(
            select(OutreachEmail).where(
                func.lower(OutreachEmail.recipient_email) == email,
                OutreachEmail.status != "bounced",
            )
        )
        for row in result.scalars().all():
            row.status = "bounced"
            await _record_event(db, row.id, "bounced", metadata={"source": "imap-sync"})
            marked += 1

    if marked:
        await db.commit()
    return marked


# ---------------------------------------------------------------------------
# Outreach analytics
# ---------------------------------------------------------------------------


async def get_outreach_stats(db: AsyncSession) -> dict[str, Any]:
    """Aggregate outreach metrics."""
    result = await db.execute(
        select(OutreachEmail.status, func.count(OutreachEmail.id)).group_by(
            OutreachEmail.status
        )
    )
    counts: dict[str, int] = {status: int(cnt) for status, cnt in result.all()}

    total_sent = counts.get("sent", 0) + counts.get("opened", 0) + counts.get("replied", 0)
    opened = counts.get("opened", 0)
    replied = counts.get("replied", 0)
    bounced = counts.get("bounced", 0)
    failed = counts.get("failed", 0)
    queued = counts.get("queued", 0)
    draft = counts.get("draft", 0)

    return {
        "counts": counts,
        "total_sent": total_sent,
        "opened": opened,
        "replied": replied,
        "bounced": bounced,
        "failed": failed,
        "queued": queued,
        "draft": draft,
        "open_rate": round(opened / total_sent * 100, 2) if total_sent else 0.0,
        "reply_rate": round(replied / total_sent * 100, 2) if total_sent else 0.0,
        "bounce_rate": round(bounced / (total_sent + bounced) * 100, 2)
        if (total_sent + bounced)
        else 0.0,
        "sent_today": await count_sent_today(db),
        "daily_cap": get_settings().outreach_daily_cap,
    }


async def get_outreach_funnel(db: AsyncSession) -> list[dict[str, Any]]:
    """Return a funnel breakdown from sent → opened → replied."""
    stats = await get_outreach_stats(db)
    sent = stats["total_sent"]
    opened = stats["opened"]
    replied = stats["replied"]
    return [
        {
            "stage": "sent",
            "count": sent,
            "conversion_pct": 100.0,
        },
        {
            "stage": "opened",
            "count": opened,
            "conversion_pct": round(opened / sent * 100, 2) if sent else 0.0,
        },
        {
            "stage": "replied",
            "count": replied,
            "conversion_pct": round(replied / sent * 100, 2) if sent else 0.0,
        },
    ]


# ---------------------------------------------------------------------------
# Bulk helpers
# ---------------------------------------------------------------------------


async def enqueue_many(
    db: AsyncSession,
    *,
    template_id: int,
    recipients: list[dict[str, str]],
    application_id: int | None = None,
    strategy: AbsStrategy | str = AbsStrategy.BEST,
    skip_duplicates: bool = True,
) -> dict[str, Any]:
    """Compose + queue emails for multiple recipients.

    ``recipients`` is a list of dicts with keys ``email``, ``company``,
    ``founder_name``, ``trigger`` (any keys supported by the template).

    Returns counts of created / skipped / failed.
    """
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError(f"Template {template_id} not found")

    created = 0
    skipped = 0
    failed = 0

    for entry in recipients:
        email_addr = (entry.get("email") or "").strip()
        if not email_addr:
            continue

        if skip_duplicates:
            dedup = await dedup_check(db, email_addr)
            if dedup is not DedupResult.OK:
                skipped += 1
                continue

        try:
            email, _chosen = await compose_from_template(
                db,
                recipient_email=email_addr,
                template_id=template_id,
                variables=entry,
                application_id=application_id,
                strategy=strategy,
            )
            await enqueue(db, email.id)
            created += 1
        except Exception:
            logger.exception("Failed to enqueue to %s", email_addr)
            failed += 1

    return {"created": created, "skipped": skipped, "failed": failed}


async def send_bulk(
    db: AsyncSession,
    *,
    template_id: int,
    recipients: list[dict[str, str]],
    strategy: AbsStrategy | str = AbsStrategy.BEST,
    attachments: list[Path] | None = None,
) -> list[dict[str, Any]]:
    """Compose and immediately send to a list of recipients.

    Respects rate limits — stops when the cap or interval blocks.
    """
    results: list[dict[str, Any]] = []
    settings = get_settings()

    for entry in recipients:
        email_addr = (entry.get("email") or "").strip()
        if not email_addr:
            continue

        dedup = await dedup_check(db, email_addr)
        if dedup is not DedupResult.OK:
            results.append({
                "email": email_addr,
                "status": "skipped",
                "reason": dedup.value,
            })
            continue

        allowed, info = await rate_limit_ok(db)
        if not allowed:
            results.append({
                "email": email_addr,
                "status": "rate_limited",
                "reason": info.get("reason"),
            })
            break

        try:
            email, _chosen = await compose_from_template(
                db,
                recipient_email=email_addr,
                template_id=template_id,
                variables=entry,
                strategy=strategy,
            )
            result = await send_now(db, email.id, attachments=attachments)
            results.append({"email": email_addr, **result})
        except Exception as exc:
            results.append({"email": email_addr, "status": "error", "error": str(exc)})

        if settings.outreach_min_interval_seconds:
            delay = random.uniform(
                settings.outreach_min_interval_seconds,
                settings.outreach_min_interval_seconds * 2,
            )
            await asyncio.sleep(delay)

    return results


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


async def prune_old_drafts(db: AsyncSession, *, older_than_days: int = 30) -> int:
    """Delete drafts older than ``older_than_days``."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    result = await db.execute(
        select(OutreachEmail).where(
            OutreachEmail.status == "draft",
            OutreachEmail.created_at < cutoff,
        )
    )
    drafts = list(result.scalars().all())
    for email in drafts:
        await db.delete(email)
    await db.commit()
    return len(drafts)


async def retry_failed(db: AsyncSession, email_id: int) -> bool:
    """Move a ``failed`` email back to draft so it can be retried."""
    email = await db.get(OutreachEmail, email_id)
    if email is None or email.status != "failed":
        return False
    email.status = "draft"
    await db.commit()
    await _record_event(db, email.id, "retry")
    await db.commit()
    return True
