"""Email template service — CRUD, A/B selection, interpolation, tracking."""

from __future__ import annotations

import random
import re
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.email_template import EmailTemplate
from app.models.outreach_email import OutreachEmail
from app.schemas.template import EmailTemplateCreate, EmailTemplateUpdate

ABStrategy = Literal["best", "random"]

# {var_name} — letters, digits, underscores; must start with a letter or underscore
VAR_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

# Minimum uses before a variant's reply_rate is considered meaningful
MIN_USAGE_FOR_BEST = 3


# ---------------------------------------------------------------------------
# CRUD  (signatures preserved for api/v1/templates.py)
# ---------------------------------------------------------------------------


async def list_templates(db: AsyncSession) -> list[EmailTemplate]:
    """Return all email templates ordered by name."""
    result = await db.execute(select(EmailTemplate).order_by(EmailTemplate.name))
    return list(result.scalars().all())


async def create_template(db: AsyncSession, payload: EmailTemplateCreate) -> EmailTemplate:
    """Create a new email template."""
    template = EmailTemplate(**payload.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def update_template(
    db: AsyncSession, template_id: int, payload: EmailTemplateUpdate
) -> EmailTemplate | None:
    """Partially update a template, returning None if not found."""
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        return None
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    await db.commit()
    await db.refresh(template)
    return template


# ---------------------------------------------------------------------------
# Variable interpolation
# ---------------------------------------------------------------------------


def interpolate(template: str, variables: dict[str, str]) -> str:
    """Replace ``{var}`` placeholders with values from *variables*.

    Unknown placeholders are left intact (no ``KeyError``); extra keys in
    *variables* are silently ignored. This keeps rendering fault-tolerant
    when a template is previewed with a partial context.
    """
    return VAR_PATTERN.sub(lambda m: str(variables.get(m.group(1), m.group(0))), template)


def interpolate_template(
    template: EmailTemplate, variables: dict[str, str]
) -> tuple[str, str]:
    """Return ``(subject, body)`` with variables interpolated."""
    return (
        interpolate(template.subject_template, variables),
        interpolate(template.body_template, variables),
    )


# ---------------------------------------------------------------------------
# A/B selection
# ---------------------------------------------------------------------------


async def get_ab_variants(db: AsyncSession, ab_group_id: str) -> list[EmailTemplate]:
    """Return every template belonging to an A/B group, ordered by variant."""
    result = await db.execute(
        select(EmailTemplate)
        .where(EmailTemplate.ab_group_id == ab_group_id)
        .order_by(EmailTemplate.ab_variant)
    )
    return list(result.scalars().all())


async def select_template(
    db: AsyncSession,
    ab_group_id: str,
    strategy: ABStrategy = "best",
) -> EmailTemplate | None:
    """Select a variant from an A/B group.

    * ``best``   — highest ``reply_rate`` among variants with at least
      ``MIN_USAGE_FOR_BEST`` uses; falls back to random when no variant
      yet has enough data.
    * ``random``  — uniform random pick across the group.
    """
    variants = await get_ab_variants(db, ab_group_id)
    if not variants:
        return None
    if len(variants) == 1 or strategy == "random":
        return random.choice(variants)

    qualified = [
        v for v in variants
        if v.usage_count >= MIN_USAGE_FOR_BEST and v.reply_rate is not None
    ]
    if qualified:
        return max(qualified, key=lambda v: v.reply_rate)  # type: ignore[arg-type,return-value]
    return random.choice(variants)


# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------


async def record_usage(db: AsyncSession, template_id: int) -> None:
    """Increment a template's ``usage_count`` by one."""
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        return
    template.usage_count += 1
    await db.commit()


async def update_reply_rate(db: AsyncSession, template_id: int) -> None:
    """Recalculate ``reply_rate`` from linked ``OutreachEmail`` records.

    ``reply_rate`` is the percentage of sent emails (linked to this template)
    that have a non-null ``replied_at``. It is stored denormalized on the
    template for fast A/B ranking.
    """
    result = await db.execute(
        select(
            func.count().label("total"),
            func.count(OutreachEmail.replied_at).label("replied"),
        ).where(OutreachEmail.template_id == template_id)
    )
    row = result.one()
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        return
    template.reply_rate = (row.replied / row.total * 100) if row.total > 0 else None
    await db.commit()


async def recalculate_all_reply_rates(db: AsyncSession) -> None:
    """Batch-recalculate ``reply_rate`` for every template (maintenance hook)."""
    result = await db.execute(
        select(
            OutreachEmail.template_id,
            func.count().label("total"),
            func.count(OutreachEmail.replied_at).label("replied"),
        )
        .where(OutreachEmail.template_id.isnot(None))
        .group_by(OutreachEmail.template_id)
    )
    for template_id, total, replied in result.all():
        template = await db.get(EmailTemplate, template_id)
        if template is not None:
            template.reply_rate = (replied / total * 100) if total > 0 else None
    await db.commit()


# ---------------------------------------------------------------------------
# Compose helpers
# ---------------------------------------------------------------------------


async def compose(
    db: AsyncSession,
    template_id: int,
    variables: dict[str, str],
    *,
    track_usage: bool = True,
) -> tuple[EmailTemplate, str, str]:
    """Load a template by id, interpolate variables, optionally track usage.

    Returns ``(template, subject, body)``. Raises ``NotFoundError`` when the
    template does not exist.
    """
    template = await db.get(EmailTemplate, template_id)
    if template is None:
        raise NotFoundError(f"Template {template_id} not found")
    subject, body = interpolate_template(template, variables)
    if track_usage:
        template.usage_count += 1
        await db.commit()
    return template, subject, body


async def compose_with_ab(
    db: AsyncSession,
    ab_group_id: str,
    variables: dict[str, str],
    *,
    strategy: ABStrategy = "best",
) -> tuple[EmailTemplate, str, str]:
    """Select an A/B variant, interpolate variables, and track usage.

    Returns ``(template, subject, body)``. Raises ``NotFoundError`` when the
    group has no variants.
    """
    template = await select_template(db, ab_group_id, strategy)
    if template is None:
        raise NotFoundError(f"No templates in A/B group '{ab_group_id}'")
    subject, body = interpolate_template(template, variables)
    template.usage_count += 1
    await db.commit()
    return template, subject, body


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


async def get_ab_stats(db: AsyncSession, ab_group_id: str) -> list[dict]:
    """Return live performance stats for every variant in an A/B group.

    Stats are computed from ``OutreachEmail`` rows rather than the
    denormalized columns, so they always reflect current outcomes.
    """
    variants = await get_ab_variants(db, ab_group_id)
    stats: list[dict] = []
    for v in variants:
        result = await db.execute(
            select(
                func.count().label("total"),
                func.count(OutreachEmail.replied_at).label("replied"),
            ).where(OutreachEmail.template_id == v.id)
        )
        row = result.one()
        total = row.total
        replied = row.replied
        stats.append(
            {
                "template_id": v.id,
                "variant": v.ab_variant,
                "name": v.name,
                "usage_count": v.usage_count,
                "total_sent": total,
                "total_replied": replied,
                "reply_rate": (replied / total * 100) if total > 0 else None,
            }
        )
    return stats
