"""Tests for the legacy data migration script.

The migration DB persists across tests (session scope). The first test that
runs `run_migration` populates the DB; subsequent tests verify idempotency
by asserting stats counters are zero while DB counts stay stable.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.migrations.migrate_json import run_migration
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

TEST_DB_PATH = Path(__file__).resolve().parent / "test_migrate_careeros.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

_first_run_stats: dict[str, int] = {}


@pytest.fixture(scope="session", autouse=True)
async def _setup_db():
    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)

    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_migration_populates_database(db_session: AsyncSession) -> None:
    """First run should create all entity types and report positive stats."""
    stats = await run_migration(database_url=TEST_DATABASE_URL)
    _first_run_stats.update(
        companies=stats.companies_created,
        contacts=stats.contacts_created,
        jobs=stats.job_postings_created,
        applications=stats.applications_created,
        emails=stats.outreach_emails_created,
        templates=stats.email_templates_created,
        events=stats.email_events_created,
    )

    company_count = (
        await db_session.execute(select(func.count()).select_from(Company))
    ).scalar_one()
    job_count = (
        await db_session.execute(select(func.count()).select_from(JobPosting))
    ).scalar_one()
    contact_count = (
        await db_session.execute(select(func.count()).select_from(Contact))
    ).scalar_one()
    email_count = (
        await db_session.execute(select(func.count()).select_from(OutreachEmail))
    ).scalar_one()
    tmpl_count = (
        await db_session.execute(select(func.count()).select_from(EmailTemplate))
    ).scalar_one()
    event_count = (
        await db_session.execute(select(func.count()).select_from(EmailEvent))
    ).scalar_one()

    assert company_count > 0, "No companies created"
    assert job_count > 0, "No job postings created"
    assert contact_count > 0, "No contacts created"
    assert email_count > 0, "No outreach emails created"
    assert tmpl_count > 0, "No email templates created"
    assert event_count > 0, "No email events created"

    # Stats should match DB counts on first run
    assert stats.companies_created == company_count
    assert stats.job_postings_created == job_count
    assert stats.contacts_created == contact_count
    assert stats.outreach_emails_created == email_count
    assert stats.email_templates_created == tmpl_count
    assert stats.email_events_created == event_count


@pytest.mark.asyncio
async def test_migration_is_idempotent(db_session: AsyncSession) -> None:
    """Running migration again must create zero new records."""
    second_stats = await run_migration(database_url=TEST_DATABASE_URL)

    # Second run should create nothing new
    assert second_stats.companies_created == 0
    assert second_stats.contacts_created == 0
    assert second_stats.job_postings_created == 0
    assert second_stats.applications_created == 0
    assert second_stats.outreach_emails_created == 0
    assert second_stats.email_templates_created == 0
    assert second_stats.email_events_created == 0

    # DB counts should match the first run's stats
    company_count = (
        await db_session.execute(select(func.count()).select_from(Company))
    ).scalar_one()
    assert company_count == _first_run_stats["companies"]


@pytest.mark.asyncio
async def test_migration_links_applications_to_jobs(
    db_session: AsyncSession,
) -> None:
    apps_with_jobs = (
        await db_session.execute(
            select(func.count()).select_from(Application).where(
                Application.job_posting_id.is_not(None)
            )
        )
    ).scalar_one()
    assert apps_with_jobs > 0


@pytest.mark.asyncio
async def test_migration_flags_bounced_emails(db_session: AsyncSession) -> None:
    bounced_count = (
        await db_session.execute(
            select(func.count()).select_from(OutreachEmail).where(
                OutreachEmail.status == "bounced"
            )
        )
    ).scalar_one()
    # bounced_emails.json has 7 entries
    assert bounced_count >= 7


@pytest.mark.asyncio
async def test_migration_stats_summary() -> None:
    stats = await run_migration(database_url=TEST_DATABASE_URL)

    summary = stats.summary()
    assert "Migration complete" in summary
    assert "companies" in summary
    assert "contacts" in summary
    assert "jobs" in summary
    assert stats.rows_skipped >= 0
