"""Migrate legacy JSON/CSV data into the CareerOS SQLite database.

Reads the existing data/ files (leads.csv, contacted_emails.json,
bounced_emails.json, ab_templates.json, ab_outcomes.json) and inserts
them into the corresponding SQLAlchemy tables, de-duplicating on natural
keys so the migration is safe to run repeatedly.

Run with:
    cd careeros-backend && python3 -m app.seed.legacy_data
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app.config.settings import get_settings
from app.database import AsyncSessionLocal
from app.models import (
    Application,
    ApplicationStatus,
    Base,
    Company,
    EmailTemplate,
    JobPosting,
    OutreachEmail,
)

# Project root (where the data/ folder lives) is two levels up from this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_or_create_company(session, name: str, domain: str | None = None) -> Company:
    stmt = select(Company).where(Company.name == name)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()
    if company is None:
        company = Company(name=name, domain=domain)
        session.add(company)
        await session.flush()
    return company


async def _company_exists(session, name: str) -> bool:
    stmt = select(Company.id).where(Company.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _job_exists(session, url: str | None) -> bool:
    if not url:
        return False
    stmt = select(JobPosting.id).where(JobPosting.url == url)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _email_template_exists(session, name: str) -> bool:
    stmt = select(EmailTemplate.id).where(EmailTemplate.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _contacted_email_exists(session, email: str) -> bool:
    stmt = select(OutreachEmail.id).where(OutreachEmail.recipient_email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


# ---------------------------------------------------------------------------
# Migrators
# ---------------------------------------------------------------------------

async def migrate_leads_csv(session) -> int:
    """Import data/leads.csv into companies + job_postings + applications."""
    leads_path = DATA_DIR / "leads.csv"
    if not leads_path.exists():
        print("  leads.csv not found, skipping.")
        return 0

    count = 0
    with leads_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            company_name = (row.get("company") or "").strip()
            role = (row.get("role") or "").strip()
            url = (row.get("url") or "").strip() or None
            if not company_name or not role:
                continue

            # Skip duplicates by URL
            if url and await _job_exists(session, url):
                continue

            # Find or create company
            company = await _get_or_create_company(session, company_name)

            # Determine remote_type from notes/source
            notes = (row.get("notes") or "").strip()
            remote_type: str | None = None
            if "remote" in notes.lower() or "Remote" in role:
                remote_type = "remote"

            # Create the job posting
            job = JobPosting(
                company_id=company.id,
                title=role,
                description=notes or None,
                url=url,
                remote_type=remote_type,
                portal_source=(row.get("source") or None),
                status="discovered",
                discovered_at=datetime.utcnow(),
            )
            session.add(job)
            await session.flush()

            # Create an application if status indicates contact
            status_text = (row.get("status") or "contacted").strip().lower()
            if status_text in ("contacted", "replied", "responded"):
                app_status: ApplicationStatus = "applied"
                applied_at = datetime.utcnow().date()
                session.add(
                    Application(
                        job_posting_id=job.id,
                        status=app_status,
                        applied_date=applied_at,
                        notes=f"email_source={row.get('email_source', '')}",
                    )
                )

            count += 1

    await session.flush()
    return count


async def migrate_templates(session, filename: str = "ab_templates.json") -> int:
    """Import A/B email templates into email_templates."""
    path = DATA_DIR / filename
    if not path.exists():
        print(f"  {filename} not found, skipping.")
        return 0

    raw = json.loads(path.read_text(encoding="utf-8"))
    templates = raw if isinstance(raw, list) else [raw]

    count = 0
    for tpl in templates:
        name = (tpl.get("name") or tpl.get("template_id") or "").strip()
        if not name or await _email_template_exists(session, name):
            continue

        session.add(
            EmailTemplate(
                name=name,
                subject_template=tpl.get("subject", ""),
                body_template=tpl.get("body", ""),
                language="en",
                is_ab_test="ab_variant" in tpl,
                ab_variant=tpl.get("ab_variant"),
                usage_count=int(tpl.get("usage_count", 0) or 0),
            )
        )
        count += 1

    await session.flush()
    return count


async def migrate_contacted_emails(session, filename: str = "contacted_emails.json") -> int:
    """Import contacted email addresses as OutreachEmail records (sent status)."""
    path = DATA_DIR / filename
    if not path.exists():
        print(f"  {filename} not found, skipping.")
        return 0

    emails = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(emails, list):
        return 0

    count = 0
    for addr in emails:
        addr = (addr or "").strip()
        if not addr or await _contacted_email_exists(session, addr):
            continue

        session.add(
            OutreachEmail(
                recipient_email=addr,
                subject="Legacy import",
                body="",
                status="sent",
                sent_at=datetime.utcnow(),
            )
        )
        count += 1

    await session.flush()
    return count


async def migrate_bounced_emails(session, filename: str = "bounced_emails.json") -> int:
    """Import bounced email addresses as OutreachEmail records (bounced status)."""
    path = DATA_DIR / filename
    if not path.exists():
        print(f"  {filename} not found, skipping.")
        return 0

    emails = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(emails, list):
        return 0

    count = 0
    for addr in emails:
        addr = (addr or "").strip()
        if not addr or await _contacted_email_exists(session, addr):
            continue

        session.add(
            OutreachEmail(
                recipient_email=addr,
                subject="Legacy import",
                body="",
                status="bounced",
            )
        )
        count += 1

    await session.flush()
    return count


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

async def migrate_all() -> dict[str, int]:
    """Run every migrator inside a single transaction. Returns counts per source."""
    from app.database import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    counts: dict[str, int] = {}
    async with AsyncSessionLocal() as session, session.begin():
        print("Migrating leads.csv ...")
        counts["leads"] = await migrate_leads_csv(session)

        print("Migrating A/B templates ...")
        counts["templates"] = await migrate_templates(session)

        print("Migrating contacted emails ...")
        counts["contacted_emails"] = await migrate_contacted_emails(session)

        print("Migrating bounced emails ...")
        counts["bounced_emails"] = await migrate_bounced_emails(session)

    return counts


if __name__ == "__main__":
    import asyncio

    print("CareerOS legacy data migration")
    print("=" * 40)
    settings = get_settings()
    print(f"Database: {settings.database_url}")

    result = asyncio.run(migrate_all())

    print("\nDone. Imported:")
    for key, value in result.items():
        print(f"  {key}: {value}")
