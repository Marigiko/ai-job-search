"""Shared pytest fixtures for CareerOS integration tests.

Uses in-memory SQLite (file:...?mode=memory&cache=shared) for instant
execution. Per-test isolation is achieved via SAVEPOINT (nested
transactions): each test creates a SAVEPOINT on the shared connection,
and it is rolled back at teardown.

Note: SQLite DDL (CREATE TABLE) auto-commits, so table creation happens
in a separate connection before the session transaction begins.
"""

from __future__ import annotations

import asyncio
import tempfile
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.models import Base
from app.models.company import Company
from app.models.email_template import EmailTemplate
from app.models.job_posting import JobPosting
from app.models.outreach_email import OutreachEmail

# In-memory SQLite with shared cache.
TEST_DATABASE_URL = (
    "sqlite+aiosqlite:///file:careeros_test?mode=memory&cache=shared&uri=true"
)

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False, "uri": True},
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
async def _setup_db() -> AsyncGenerator[None, None]:
    """Create tables in a separate connection (DDL auto-commits)."""
    # DDL requires its own transaction context
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest.fixture(scope="session")
async def _session_connection() -> AsyncGenerator[object, None]:
    """Single connection for the session, kept open to preserve the in-memory DB.

    A top-level transaction is started so that SAVEPOINTs work for per-test
    isolation.
    """
    async with test_engine.connect() as connection:
        # Begin the top-level transaction required for SAVEPOINTs
        await connection.begin()
        yield connection
        await connection.rollback()


@pytest.fixture
async def db_session(_session_connection) -> AsyncGenerator[AsyncSession, None]:
    """Direct database session with SAVEPOINT isolation."""
    nested = await _session_connection.begin_nested()
    session = TestSessionLocal(bind=_session_connection)
    try:
        yield session
    finally:
        await session.close()
        try:
            await nested.rollback()
        except OperationalError:
            # Savepoint may have been released by a commit
            pass


@pytest.fixture
async def client(_session_connection) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with SAVEPOINT-based isolation."""
    from app.main import create_app

    application = create_app()
    nested = await _session_connection.begin_nested()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal(bind=_session_connection) as session:
            try:
                yield session
            except Exception:
                raise

    application.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    try:
        await nested.rollback()
    except OperationalError:
        pass
    application.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Entity fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def sample_company(db_session: AsyncSession) -> Company:
    """Create a sample company for FK relationships."""
    company = Company(
        name="Acme Corp",
        domain="acme.io",
        industry="Technology",
        size="50-200",
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest.fixture
async def sample_job(db_session: AsyncSession, sample_company: Company) -> JobPosting:
    """Create a sample job posting linked to the sample company."""
    job = JobPosting(
        company_id=sample_company.id,
        title="Senior Backend Engineer",
        description="FastAPI + SQLAlchemy role",
        url="https://acme.io/careers/backend",
        salary_min=120_000,
        salary_max=160_000,
        currency="USD",
        location="Remote",
        remote_type="remote",
        visa_sponsorship=True,
        portal_source="manual",
        status="discovered",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.fixture
async def sample_jobs(db_session: AsyncSession, sample_company: Company) -> list[JobPosting]:
    """Create multiple jobs in different pipeline stages for funnel tests."""
    jobs = []
    stages = [
        ("Backend Engineer", "discovered"),
        ("Frontend Engineer", "interested"),
        ("DevOps Engineer", "applied"),
        ("Data Engineer", "screening"),
        ("ML Engineer", "interview"),
        ("Staff Engineer", "offer"),
        ("Junior Developer", "rejected"),
    ]
    for i, (title, stage) in enumerate(stages):
        job = JobPosting(
            company_id=sample_company.id,
            title=title,
            description=f"Role in {stage} stage",
            url=f"https://acme.io/careers/{i}",
            salary_min=80_000 + i * 20_000,
            salary_max=120_000 + i * 20_000,
            currency="USD",
            location="Remote",
            remote_type="remote",
            visa_sponsorship=False,
            portal_source="manual",
            status=stage,
        )
        db_session.add(job)
        jobs.append(job)
    await db_session.commit()
    for job in jobs:
        await db_session.refresh(job)
    return jobs


@pytest.fixture
async def sample_template(db_session: AsyncSession) -> EmailTemplate:
    """Create a sample non-AB email template."""
    template = EmailTemplate(
        name="Standard Outreach",
        subject_template="Application for {job_title} at {company}",
        body_template=(
            "Hi {name},\n\n"
            "I'm excited to apply for the {job_title} role at {company}. "
            "My background in Python and FastAPI makes me a strong fit.\n\n"
            "Best regards"
        ),
        language="en",
        is_ab_test=False,
        usage_count=0,
        reply_rate=None,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest.fixture
async def sample_ab_templates(db_session: AsyncSession) -> tuple[EmailTemplate, EmailTemplate]:
    """Create A/B test templates with usage stats for strategy tests."""
    template_a = EmailTemplate(
        name="AB Outreach — Variant A",
        subject_template="Quick question about {company}",
        body_template="Hi {name},\n\nVariant A body for {job_title} at {company}.\n\nBest",
        language="en",
        is_ab_test=True,
        ab_group_id="outreach_v1",
        ab_variant="A",
        usage_count=5,
        reply_rate=0.20,
    )
    template_b = EmailTemplate(
        name="AB Outreach — Variant B",
        subject_template="Excited about {company}",
        body_template="Hi {name},\n\nVariant B body for {job_title} at {company}.\n\nCheers",
        language="en",
        is_ab_test=True,
        ab_group_id="outreach_v1",
        ab_variant="B",
        usage_count=10,
        reply_rate=0.30,
    )
    db_session.add_all([template_a, template_b])
    await db_session.commit()
    for t in (template_a, template_b):
        await db_session.refresh(t)
    return template_a, template_b


@pytest.fixture
async def sample_outreach(
    db_session: AsyncSession, sample_template: EmailTemplate
) -> OutreachEmail:
    """Create a sample draft outreach email."""
    email = OutreachEmail(
        template_id=sample_template.id,
        recipient_email="founder@acme.io",
        subject="Application for Senior Backend Engineer at Acme Corp",
        body="Hi there,\n\nTest body",
        status="draft",
    )
    db_session.add(email)
    await db_session.commit()
    await db_session.refresh(email)
    return email


@pytest.fixture
async def sent_emails(
    db_session: AsyncSession, sample_template: EmailTemplate
) -> list[OutreachEmail]:
    """Create a batch of sent emails with timestamps for rate-limit tests."""
    now = datetime.now(timezone.utc)
    emails = []
    for i in range(3):
        email = OutreachEmail(
            template_id=sample_template.id,
            recipient_email=f"user{i}@example.com",
            subject=f"Subject {i}",
            body=f"Body {i}",
            status="sent",
            sent_at=now - timedelta(minutes=i * 5),
            ab_variant="A" if i % 2 == 0 else "B",
        )
        db_session.add(email)
        emails.append(email)
    await db_session.commit()
    for email in emails:
        await db_session.refresh(email)
    return emails


@pytest.fixture
def tmp_storage_dir() -> Path:
    """Temporary directory for document generation tests."""
    with tempfile.TemporaryDirectory(prefix="careeros_test_") as tmp:
        yield Path(tmp)
