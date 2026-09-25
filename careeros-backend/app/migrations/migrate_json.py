"""Legacy data migration: imports JSON/CSV files into CareerOS SQLite.

Idempotent — safe to run multiple times. Duplicate detection queries the
database on each run (via helper functions) so re-runs are always no-ops,
even when the in-memory cache starts empty.

Sources:
    - data/contacted_emails.json       -> outreach_emails (sent)
    - data/bounced_emails.json         -> outreach_emails (bounced)
    - data/leads.csv                   -> companies, job_postings, applications, contacts
    - data/ab_templates.json           -> email_templates
    - data/ab_outcomes.json            -> email_events + outreach_emails
    - job_search_tracker.csv            -> companies, job_postings, applications, outreach_emails
    - job_scraper/seen_jobs.json       -> companies, job_postings (discovered)

Run with:
    cd careeros-backend && python3 -m app.migrations.migrate_json
"""

from __future__ import annotations

import asyncio
import csv
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.models import (
    Application,
    Base,
    Company,
    Contact,
    EmailEvent,
    EmailTemplate,
    JobPosting,
    OutreachEmail,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
JOB_SCRAPER_DIR = PROJECT_ROOT / "job_scraper"

CONTACTED_EMAILS_PATH = DATA_DIR / "contacted_emails.json"
BOUNCED_EMAILS_PATH = DATA_DIR / "bounced_emails.json"
LEADS_CSV_PATH = DATA_DIR / "leads.csv"
AB_OUTCOMES_PATH = DATA_DIR / "ab_outcomes.json"
AB_TEMPLATES_PATH = DATA_DIR / "ab_templates.json"
JOB_SEARCH_TRACKER_PATH = PROJECT_ROOT / "job_search_tracker.csv"
SEEN_JOBS_PATH = JOB_SCRAPER_DIR / "seen_jobs.json"


# ---------------------------------------------------------------------------
# Migration stats
# ---------------------------------------------------------------------------


@dataclass
class MigrationStats:
    """Counters for each entity type touched during migration."""

    companies_created: int = 0
    contacts_created: int = 0
    job_postings_created: int = 0
    applications_created: int = 0
    outreach_emails_created: int = 0
    email_templates_created: int = 0
    email_events_created: int = 0
    rows_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            "Migration complete: "
            f"{self.companies_created} companies, "
            f"{self.contacts_created} contacts, "
            f"{self.job_postings_created} jobs, "
            f"{self.applications_created} applications, "
            f"{self.outreach_emails_created} emails, "
            f"{self.email_templates_created} templates, "
            f"{self.email_events_created} events created | "
            f"{self.rows_skipped} skipped | "
            f"{len(self.errors)} errors"
        )


# ---------------------------------------------------------------------------
# In-memory dedup cache (per run)
# ---------------------------------------------------------------------------


@dataclass
class DedupIndex:
    """Natural-key lookups populated from DB at start + during migration."""

    company_names: set[str] = field(default_factory=set)
    company_ids: dict[str, int] = field(default_factory=dict)
    contact_emails: set[str] = field(default_factory=set)
    job_urls: set[str] = field(default_factory=set)
    job_keys: set[tuple[str, int]] = field(default_factory=set)
    email_recipients: set[str] = field(default_factory=set)
    email_keys: set[tuple[str, str]] = field(default_factory=set)
    template_names: set[str] = field(default_factory=set)
    event_keys: set[tuple[int, str]] = field(default_factory=set)

    async def load_from_db(self, session: AsyncSession) -> None:
        """Pre-populate cache with existing records for idempotency."""
        for row in (await session.execute(select(Company))).scalars().all():
            self.company_names.add(row.name.lower())
            self.company_ids[row.name.lower()] = row.id
        for row in (await session.execute(select(Contact))).scalars().all():
            if row.email:
                self.contact_emails.add(row.email.lower())
        for row in (await session.execute(select(JobPosting))).scalars().all():
            if row.url:
                self.job_urls.add(row.url)
            self.job_keys.add((row.title.strip().lower(), row.company_id or 0))
        for row in (await session.execute(select(OutreachEmail))).scalars().all():
            self.email_recipients.add(row.recipient_email.lower())
            self.email_keys.add((row.recipient_email.lower(), row.subject))
        for row in (await session.execute(select(EmailTemplate))).scalars().all():
            self.template_names.add(row.name.strip().lower())
        for row in (await session.execute(select(EmailEvent))).scalars().all():
            self.event_keys.add((row.outreach_email_id, row.event_type))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_name(name: str) -> str:
    """Lowercase, strip, collapse whitespace for dedup."""
    return re.sub(r"\s+", " ", name.strip().lower())


def _parse_date(value: str | None) -> date | None:
    """Parse YYYY-MM-DD or return None."""
    if not value or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime or return None."""
    if not value or not value.strip():
        return None
    try:
        dt = datetime.fromisoformat(value.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _remote_type_from_text(value: str | None) -> str | None:
    """Map free-text remote flag to enum value."""
    if not value:
        return None
    v = value.strip().lower()
    if "remote" in v:
        return "remote"
    if "hybrid" in v:
        return "hybrid"
    return "onsite"


async def _upsert_company(
    session: AsyncSession,
    name: str,
    index: DedupIndex,
    stats: MigrationStats | None = None,
) -> Company | None:
    """Get existing company or create. Updates index."""
    if not name or not name.strip():
        return None
    key = _normalize_name(name)
    if key in index.company_names:
        cid = index.company_ids.get(key)
        if cid:
            return await session.get(Company, cid)
        return None

    company = Company(name=name.strip())
    session.add(company)
    await session.flush()
    index.company_names.add(key)
    index.company_ids[key] = company.id
    if stats is not None:
        stats.companies_created += 1
    return company


# ---------------------------------------------------------------------------
# Migration: A/B templates (must run before outcomes)
# ---------------------------------------------------------------------------


async def migrate_ab_templates(
    session: AsyncSession,
    stats: MigrationStats,
    index: DedupIndex,
) -> None:
    """Import data/ab_templates.json into email_templates."""
    if not AB_TEMPLATES_PATH.exists():
        logger.warning("AB templates file not found: %s", AB_TEMPLATES_PATH)
        return

    raw: dict[str, dict[str, str]] = json.loads(
        AB_TEMPLATES_PATH.read_text(encoding="utf-8")
    )
    logger.info("Loading %d AB templates", len(raw))

    for _group_id, tmpl in raw.items():
        name = (tmpl.get("name") or "").strip()
        if not name:
            stats.rows_skipped += 1
            continue
        key = name.lower()
        if key in index.template_names:
            stats.rows_skipped += 1
            continue

        template = EmailTemplate(
            name=name,
            subject_template=tmpl.get("subject", ""),
            body_template=tmpl.get("body", ""),
            language="en",
            is_ab_test=True,
            ab_variant="A",
        )
        session.add(template)
        await session.flush()
        index.template_names.add(key)
        stats.email_templates_created += 1
        logger.debug("Created template: %s", name)


# ---------------------------------------------------------------------------
# Migration: seen_jobs.json -> companies + job_postings
# ---------------------------------------------------------------------------


async def migrate_seen_jobs(
    session: AsyncSession,
    stats: MigrationStats,
    index: DedupIndex,
) -> None:
    """Import job_scraper/seen_jobs.json as discovered job_postings."""
    if not SEEN_JOBS_PATH.exists():
        logger.warning("Seen-jobs file not found: %s", SEEN_JOBS_PATH)
        return

    raw: dict[str, dict[str, Any]] = json.loads(
        SEEN_JOBS_PATH.read_text(encoding="utf-8")
    )
    seen = raw.get("seen", {})
    logger.info("Loading %d seen jobs", len(seen))

    for _key, entry in seen.items():
        title = (entry.get("title") or "").strip()
        company_name = entry.get("company")
        url = entry.get("url")
        if not title:
            stats.rows_skipped += 1
            continue

        company = await _upsert_company(session, company_name, index, stats)
        company_id = company.id if company else None
        title_key = (title.lower(), company_id or 0)

        # Dedup by URL or (title, company_id)
        if url and url in index.job_urls:
            stats.rows_skipped += 1
            continue
        if title_key in index.job_keys:
            stats.rows_skipped += 1
            continue

        job = JobPosting(
            title=title,
            company_id=company_id,
            url=url,
            portal_source="scraper",
            status="discovered",
            discovered_at=_parse_date(entry.get("first_seen")),
            raw_data={"fit": entry.get("fit"), "legacy_status": entry.get("status")},
        )
        session.add(job)
        await session.flush()
        if url:
            index.job_urls.add(url)
        index.job_keys.add(title_key)
        stats.job_postings_created += 1
        logger.debug("Created job from seen_jobs: %s @ %s", title, company_name)


# ---------------------------------------------------------------------------
# Migration: leads.csv
# ---------------------------------------------------------------------------


async def migrate_leads_csv(
    session: AsyncSession,
    stats: MigrationStats,
    index: DedupIndex,
) -> None:
    """Import data/leads.csv."""
    if not LEADS_CSV_PATH.exists():
        logger.warning("Leads CSV not found: %s", LEADS_CSV_PATH)
        return

    rows: list[dict[str, str]] = []
    with LEADS_CSV_PATH.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    logger.info("Loading %d leads", len(rows))

    for row in rows:
        try:
            await _migrate_lead_row(session, row, stats, index)
        except Exception as exc:
            stats.errors.append(f"lead row {row.get('id', '?')}: {exc}")
            logger.exception("Failed to migrate lead row")


async def _migrate_lead_row(
    session: AsyncSession,
    row: dict[str, str],
    stats: MigrationStats,
    index: DedupIndex,
) -> None:
    """Migrate a single lead row."""
    company_name = (row.get("company") or "").strip()
    title = (row.get("role") or "").strip()
    url = (row.get("url") or "").strip() or None
    email = (row.get("email") or "").strip()

    if not company_name or not title:
        stats.rows_skipped += 1
        return

    company = await _upsert_company(session, company_name, index, stats)
    company_id = company.id if company else None
    title_key = (title.lower(), company_id or 0)

    # Dedup job posting
    if url and url in index.job_urls:
        stats.rows_skipped += 1
        return
    if title_key in index.job_keys:
        stats.rows_skipped += 1
        return

    notes = (row.get("notes") or "").strip()
    job = JobPosting(
        title=title,
        company_id=company_id,
        url=url,
        portal_source=(row.get("source") or None),
        status="contacted" if row.get("status") == "contacted" else "discovered",
        discovered_at=_parse_date(row.get("date_found")),
        applied_at=_parse_date(row.get("date_contacted")),
        notes=notes or None,
    )
    session.add(job)
    await session.flush()
    if url:
        index.job_urls.add(url)
    index.job_keys.add(title_key)
    stats.job_postings_created += 1

    # Application
    status_text = (row.get("status") or "contacted").strip().lower()
    if status_text in ("contacted", "replied", "responded"):
        app = Application(
            job_posting_id=job.id,
            status="applied",
            applied_date=_parse_date(row.get("date_contacted")),
            notes=f"email_source={row.get('email_source', '')}",
        )
        session.add(app)
        await session.flush()
        stats.applications_created += 1

    # Contact
    if email:
        email_key = email.lower()
        if email_key not in index.contact_emails:
            contact = Contact(
                company_id=company_id,
                email=email_key,
                is_recruiter="recruiter" in notes.lower(),
                source=row.get("email_source"),
            )
            session.add(contact)
            await session.flush()
            index.contact_emails.add(email_key)
            stats.contacts_created += 1


# ---------------------------------------------------------------------------
# Migration: job_search_tracker.csv
# ---------------------------------------------------------------------------


async def migrate_job_search_tracker(
    session: AsyncSession,
    stats: MigrationStats,
    index: DedupIndex,
) -> None:
    """Import job_search_tracker.csv."""
    if not JOB_SEARCH_TRACKER_PATH.exists():
        logger.warning("Job search tracker not found: %s", JOB_SEARCH_TRACKER_PATH)
        return

    rows: list[dict[str, str]] = []
    with JOB_SEARCH_TRACKER_PATH.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    logger.info("Loading %d tracker rows", len(rows))

    for row in rows:
        try:
            await _migrate_tracker_row(session, row, stats, index)
        except Exception as exc:
            stats.errors.append(f"tracker row {row.get('company', '?')}: {exc}")
            logger.exception("Failed to migrate tracker row")


async def _migrate_tracker_row(
    session: AsyncSession,
    row: dict[str, str],
    stats: MigrationStats,
    index: DedupIndex,
) -> None:
    """Migrate a single tracker row."""
    company_name = (row.get("company") or "").strip()
    title = (row.get("role") or "").strip()
    url = (row.get("application_url") or "").strip() or None
    status = (row.get("status") or "applied").strip().lower()

    if not company_name or not title:
        stats.rows_skipped += 1
        return

    company = await _upsert_company(session, company_name, index, stats)
    company_id = company.id if company else None
    title_key = (title.lower(), company_id or 0)

    # Dedup job posting
    if url and url in index.job_urls:
        stats.rows_skipped += 1
        return
    if title_key in index.job_keys:
        stats.rows_skipped += 1
        return

    notes = (row.get("notes") or "").strip()
    job = JobPosting(
        title=title,
        company_id=company_id,
        url=url,
        remote_type=_remote_type_from_text(row.get("relocation_visa")),
        portal_source=(row.get("source") or None),
        status="applied" if status == "applied" else "interested",
        discovered_at=_parse_date(row.get("date")),
        applied_at=_parse_date(row.get("date")) if status == "applied" else None,
        notes=notes or None,
        raw_data={
            "sector": row.get("sector"),
            "role_type": row.get("role_type"),
            "fit_rating": row.get("fit_rating"),
            "salary_expected": row.get("salary_expected"),
            "salary_offered": row.get("salary_offered"),
            "cv_file": row.get("cv_file"),
            "cover_letter_file": row.get("cover_letter_file"),
            "contact_person": row.get("contact_person"),
        },
    )
    session.add(job)
    await session.flush()
    if url:
        index.job_urls.add(url)
    index.job_keys.add(title_key)
    stats.job_postings_created += 1

    # Application (unique per job_posting_id)
    app = Application(
        job_posting_id=job.id,
        status="applied" if status == "applied" else "interested",
        applied_date=_parse_date(row.get("date")) if status == "applied" else None,
        notes=notes or None,
    )
    session.add(app)
    await session.flush()
    stats.applications_created += 1

    # Outreach email
    email = (row.get("application_url") or "").replace("mailto:", "").strip()
    if email and "@" in email:
        email_key = email.lower()
        subject = f"Application: {title}" if title else "Job Application"
        dedup_key = (email_key, subject)
        if dedup_key not in index.email_keys:
            out = OutreachEmail(
                recipient_email=email_key,
                subject=subject,
                body="",
                status="sent" if status == "applied" else "draft",
                sent_at=datetime.now(timezone.utc) if status == "applied" else None,
            )
            session.add(out)
            await session.flush()
            index.email_recipients.add(email_key)
            index.email_keys.add(dedup_key)
            stats.outreach_emails_created += 1


# ---------------------------------------------------------------------------
# Migration: contacted_emails.json
# ---------------------------------------------------------------------------


async def migrate_contacted_emails(
    session: AsyncSession,
    stats: MigrationStats,
    index: DedupIndex,
) -> None:
    """Import data/contacted_emails.json as sent outreach_emails."""
    if not CONTACTED_EMAILS_PATH.exists():
        logger.warning("Contacted emails file not found: %s", CONTACTED_EMAILS_PATH)
        return

    emails: list[str] = json.loads(CONTACTED_EMAILS_PATH.read_text(encoding="utf-8"))
    logger.info("Loading %d contacted emails", len(emails))

    for email in emails:
        email = (email or "").strip().lower()
        if not email or "@" not in email:
            stats.rows_skipped += 1
            continue
        if email in index.email_recipients:
            stats.rows_skipped += 1
            continue

        out = OutreachEmail(
            recipient_email=email,
            subject="Legacy import",
            body="",
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
        session.add(out)
        await session.flush()
        index.email_recipients.add(email)
        stats.outreach_emails_created += 1


# ---------------------------------------------------------------------------
# Migration: bounced_emails.json
# ---------------------------------------------------------------------------


async def migrate_bounced_emails(
    session: AsyncSession,
    stats: MigrationStats,
    index: DedupIndex,
) -> None:
    """Import data/bounced_emails.json — marks existing or creates bounced records."""
    if not BOUNCED_EMAILS_PATH.exists():
        logger.warning("Bounced emails file not found: %s", BOUNCED_EMAILS_PATH)
        return

    emails: list[str] = json.loads(BOUNCED_EMAILS_PATH.read_text(encoding="utf-8"))
    logger.info("Loading %d bounced emails", len(emails))

    for email in emails:
        email = (email or "").strip().lower()
        if not email or "@" not in email:
            stats.rows_skipped += 1
            continue

        # If any record (sent or already bounced) exists, ensure at least one
        # is marked bounced and skip creation.
        if email in index.email_recipients:
            result = await session.execute(
                select(OutreachEmail).where(
                    OutreachEmail.recipient_email == email,
                    OutreachEmail.status != "bounced",
                )
            )
            existing = result.scalars().first()
            if existing is not None:
                existing.status = "bounced"
                logger.debug("Marked existing email as bounced: %s", email)
            stats.rows_skipped += 1
            continue

        out = OutreachEmail(
            recipient_email=email,
            subject="Bounced",
            body="",
            status="bounced",
        )
        session.add(out)
        await session.flush()
        index.email_recipients.add(email)
        stats.outreach_emails_created += 1


# ---------------------------------------------------------------------------
# Migration: ab_outcomes.json
# ---------------------------------------------------------------------------


async def migrate_ab_outcomes(
    session: AsyncSession,
    stats: MigrationStats,
    index: DedupIndex,
) -> None:
    """Import data/ab_outcomes.json — creates placeholder outreach + events."""
    if not AB_OUTCOMES_PATH.exists():
        logger.warning("AB outcomes file not found: %s", AB_OUTCOMES_PATH)
        return

    outcomes: list[dict[str, Any]] = json.loads(
        AB_OUTCOMES_PATH.read_text(encoding="utf-8")
    )
    logger.info("Loading %d AB outcomes", len(outcomes))

    for outcome in outcomes:
        template_id = (outcome.get("template_id") or "unknown").strip()
        placeholder_email = f"{template_id}@legacy.local"
        dedup_key = (placeholder_email, "Legacy outcome")

        result = await session.execute(
            select(OutreachEmail).where(
                OutreachEmail.recipient_email == placeholder_email
            )
        )
        outreach = result.scalars().first()

        if outreach is None:
            if dedup_key in index.email_keys:
                stats.rows_skipped += 1
                continue
            ts = _parse_datetime(outcome.get("timestamp")) or datetime.now(timezone.utc)
            outreach = OutreachEmail(
                recipient_email=placeholder_email,
                subject="Legacy outcome",
                body="",
                status=outcome.get("status", "sent"),
                sent_at=ts,
            )
            session.add(outreach)
            await session.flush()
            index.email_recipients.add(placeholder_email)
            index.email_keys.add(dedup_key)
            stats.outreach_emails_created += 1

        event_key = (outreach.id, outcome.get("status", "sent"))
        if event_key in index.event_keys:
            stats.rows_skipped += 1
            continue

        event_ts = _parse_datetime(outcome.get("timestamp")) or datetime.now(timezone.utc)
        event = EmailEvent(
            outreach_email_id=outreach.id,
            event_type=outcome.get("status", "sent"),
            created_at=event_ts,
        )
        session.add(event)
        await session.flush()
        index.event_keys.add(event_key)
        stats.email_events_created += 1


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def run_migration(
    database_url: str | None = None,
) -> MigrationStats:
    """Execute the full migration pipeline.

    Args:
        database_url: Override the database URL. Defaults to settings.
    """
    settings = get_settings()
    configure_logging(settings.log_level)

    url = database_url or settings.database_url
    logger.info("Starting legacy data migration -> %s", url)

    engine = create_async_engine(url, future=True, echo=False)
    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )

    # Ensure tables exist (no-op if already created)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    stats = MigrationStats()
    index = DedupIndex()

    async with session_factory() as session, session.begin():
        await index.load_from_db(session)
        await migrate_ab_templates(session, stats, index)
        await migrate_seen_jobs(session, stats, index)
        await migrate_leads_csv(session, stats, index)
        await migrate_job_search_tracker(session, stats, index)
        await migrate_contacted_emails(session, stats, index)
        await migrate_bounced_emails(session, stats, index)
        await migrate_ab_outcomes(session, stats, index)

    await engine.dispose()

    logger.info(stats.summary())
    if stats.errors:
        for err in stats.errors:
            logger.error("  x %s", err)

    return stats


if __name__ == "__main__":
    import sys

    print("CareerOS legacy data migration")
    print("=" * 40)
    result = asyncio.run(run_migration())
    print(result.summary())
    if result.errors:
        print("Warnings:")
        for err in result.errors:
            print(f"  - {err}")
    sys.exit(0)
