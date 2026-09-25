"""Settings endpoints — SMTP, API keys, outreach limits, portals, A/B tests."""

from __future__ import annotations

import smtplib
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.email_template import EmailTemplate
from app.models.outreach_email import OutreachEmail
from app.schemas.common import MessageResponse
from app.schemas.settings import (
    AbTestPerformance,
    ApiKeys,
    ApiKeysUpdate,
    OutreachLimits,
    OutreachLimitsUpdate,
    PortalToggle,
    SettingsBundle,
    SmtpConfig,
    SmtpConfigUpdate,
)
from app.services import setting_service

router = APIRouter()


def _mask_secret(value: str) -> str:
    """Mask a secret for API responses — never return plaintext passwords."""
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * 12 + value[-4:]


def _redact_smtp(smtp: dict[str, Any]) -> SmtpConfig:
    """Return SMTP config with password masked."""
    data = dict(smtp)
    data["password"] = _mask_secret(data.get("password", ""))
    return SmtpConfig(**data)


# ── Bundle ───────────────────────────────────────────────────────────────────


@router.get("", response_model=SettingsBundle)
async def get_settings(db: AsyncSession = Depends(get_db)) -> SettingsBundle:
    """Return the full settings bundle."""
    raw = await setting_service.get_all_settings(db)
    enabled_map = await setting_service.get_portal_enabled_map(db)

    portals = [
        PortalToggle(
            id=p["id"],
            name=p["name"],
            enabled=enabled_map.get(p["id"], True),
            description=p["description"],
            category=p["category"],
        )
        for p in setting_service.PORTAL_REGISTRY
    ]

    return SettingsBundle(
        smtp=_redact_smtp(raw.get("smtp") or {}),
        api_keys=ApiKeys(
            **{k: _mask_secret(v) for k, v in (raw.get("api_keys") or {}).items()}
        ),
        outreach_limits=OutreachLimits(**(raw.get("outreach_limits") or {})),
        portals=portals,
    )


# ── SMTP ─────────────────────────────────────────────────────────────────────


@router.get("/smtp", response_model=SmtpConfig)
async def get_smtp(db: AsyncSession = Depends(get_db)) -> SmtpConfig:
    """Return SMTP configuration (password masked)."""
    raw = await setting_service.get_json_setting(db, "smtp")
    return _redact_smtp(raw or {})


@router.patch("/smtp", response_model=SmtpConfig)
async def update_smtp(
    payload: SmtpConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> SmtpConfig:
    """Update SMTP configuration."""
    current = dict(await setting_service.get_json_setting(db, "smtp") or {})
    updates = payload.model_dump(exclude_unset=True)

    # If password is the exact masked placeholder, keep the existing one
    new_password = updates.get("password")
    if new_password and new_password == _mask_secret(current.get("password", "")):
        updates["password"] = current.get("password", "")

    current.update(updates)
    await setting_service.set_json_setting(db, "smtp", current)
    await db.commit()
    return _redact_smtp(current)


@router.post("/smtp/test", response_model=MessageResponse)
async def test_smtp(db: AsyncSession = Depends(get_db)) -> MessageResponse:
    """Test SMTP connection with stored credentials."""
    raw = await setting_service.get_json_setting(db, "smtp") or {}
    host = raw.get("host", "")
    port = raw.get("port", 587)

    if not host:
        return MessageResponse(message="error", detail="SMTP host not configured")

    try:
        if raw.get("use_tls", True):
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP(host, port, timeout=10)
        server.login(raw.get("username", ""), raw.get("password", ""))
        server.quit()
        return MessageResponse(message="ok", detail="SMTP connection successful")
    except Exception as exc:
        return MessageResponse(message="error", detail=str(exc))


# ── API Keys ─────────────────────────────────────────────────────────────────


@router.get("/api-keys", response_model=ApiKeys)
async def get_api_keys(db: AsyncSession = Depends(get_db)) -> ApiKeys:
    """Return API keys."""
    raw = await setting_service.get_json_setting(db, "api_keys")
    return ApiKeys(**{k: _mask_secret(v) for k, v in (raw or {}).items()})


@router.patch("/api-keys", response_model=ApiKeys)
async def update_api_keys(
    payload: ApiKeysUpdate,
    db: AsyncSession = Depends(get_db),
) -> ApiKeys:
    """Update API keys."""
    current = dict(await setting_service.get_json_setting(db, "api_keys") or {})
    updates = payload.model_dump(exclude_unset=True)
    # If a value is the exact masked placeholder, keep the existing one
    for key, value in updates.items():
        if value and value == _mask_secret(current.get(key, "")):
            updates[key] = current.get(key, "")
    current.update(updates)
    await setting_service.set_json_setting(db, "api_keys", current)
    await db.commit()
    return ApiKeys(**{k: _mask_secret(v) for k, v in current.items()})


# ── Outreach Limits ──────────────────────────────────────────────────────────


@router.get("/outreach-limits", response_model=OutreachLimits)
async def get_outreach_limits(db: AsyncSession = Depends(get_db)) -> OutreachLimits:
    """Return outreach rate limits."""
    raw = await setting_service.get_json_setting(db, "outreach_limits")
    return OutreachLimits(**(raw or {}))


@router.patch("/outreach-limits", response_model=OutreachLimits)
async def update_outreach_limits(
    payload: OutreachLimitsUpdate,
    db: AsyncSession = Depends(get_db),
) -> OutreachLimits:
    """Update outreach rate limits."""
    current = dict(await setting_service.get_json_setting(db, "outreach_limits") or {})
    updates = payload.model_dump(exclude_unset=True)
    current.update(updates)
    await setting_service.set_json_setting(db, "outreach_limits", current)
    await db.commit()
    return OutreachLimits(**current)


# ── Portals ──────────────────────────────────────────────────────────────────


@router.get("/portals", response_model=list[PortalToggle])
async def get_portals(db: AsyncSession = Depends(get_db)) -> list[PortalToggle]:
    """Return portal toggles."""
    enabled_map = await setting_service.get_portal_enabled_map(db)
    return [
        PortalToggle(
            id=p["id"],
            name=p["name"],
            enabled=enabled_map.get(p["id"], True),
            description=p["description"],
            category=p["category"],
        )
        for p in setting_service.PORTAL_REGISTRY
    ]


@router.patch("/portals/{portal_id}", response_model=PortalToggle)
async def update_portal(
    portal_id: str,
    payload: dict[str, bool],
    db: AsyncSession = Depends(get_db),
) -> PortalToggle:
    """Toggle a portal on/off."""
    enabled = payload.get("enabled", True)
    await setting_service.set_portal_enabled(db, portal_id, enabled)
    await db.commit()

    portal_def = next(
        (p for p in setting_service.PORTAL_REGISTRY if p["id"] == portal_id),
        {"id": portal_id, "name": portal_id, "description": "", "category": "aggregator"},
    )
    return PortalToggle(
        id=portal_def["id"],
        name=portal_def["name"],
        enabled=enabled,
        description=portal_def["description"],
        category=portal_def["category"],
    )


# ── A/B Test Performance ────────────────────────────────────────────────────


@router.get("/ab-tests/performance", response_model=list[AbTestPerformance])
async def get_ab_test_performance(
    db: AsyncSession = Depends(get_db),
) -> list[AbTestPerformance]:
    """Return per-variant A/B test performance for email templates."""
    result = await db.execute(
        select(
            EmailTemplate.id,
            EmailTemplate.name,
            EmailTemplate.ab_variant,
            func.count(OutreachEmail.id).label("sent"),
            func.sum(
                case(
                    (OutreachEmail.status.in_(("opened", "replied")), 1),
                    else_=0,
                )
            ).label("opened"),
            func.sum(
                case((OutreachEmail.status == "replied", 1), else_=0)
            ).label("replied"),
        )
        .join(OutreachEmail, OutreachEmail.template_id == EmailTemplate.id)
        .where(EmailTemplate.is_ab_test.is_(True))
        .group_by(EmailTemplate.id)
    )

    variants: list[AbTestPerformance] = []
    for tid, name, variant, sent, opened, replied in result.all():
        sent = sent or 0
        opened = opened or 0
        replied = replied or 0
        variants.append(
            AbTestPerformance(
                template_id=tid,
                template_name=name,
                variant=variant or "default",
                sent_count=sent,
                open_rate=round(opened / sent, 4) if sent > 0 else 0.0,
                reply_rate=round(replied / sent, 4) if sent > 0 else 0.0,
            )
        )

    # Mark the best variant by reply_rate as winner
    if variants:
        best = max(variants, key=lambda v: v.reply_rate)
        for v in variants:
            v.is_winner = v.template_id == best.template_id

    return variants
