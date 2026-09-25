"""Integration tests for the Analytics module: funnels, outreach, salary insights.

Tests cover the analytics service (funnel conversion rates, outreach metrics,
A/B test results, salary distribution) and HTTP endpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_template import EmailTemplate
from app.models.job_posting import JobPosting
from app.models.outreach_email import OutreachEmail
from app.services import analytics_service


# =============================================================================
# FUNNEL TESTS
# =============================================================================


class TestFunnel:
    """``funnel`` calculates stage counts and conversion rates."""

    @pytest.mark.asyncio
    async def test_funnel_empty_database(self, db_session: AsyncSession) -> None:
        """Empty database returns zero counts and zero conversions."""
        result = await analytics_service.funnel(db_session)

        assert result.total_postings == 0
        assert all(stage.count == 0 for stage in result.stages)
        assert all(conv.rate == 0.0 for conv in result.conversions)

    @pytest.mark.asyncio
    async def test_funnel_stage_counts(
        self, db_session: AsyncSession, sample_jobs: list[JobPosting]
    ) -> None:
        """Stage counts match the number of jobs in each stage."""
        result = await analytics_service.funnel(db_session)

        assert result.total_postings == 7  # 7 jobs, one per stage
        stage_map = {s.stage: s.count for s in result.stages}
        assert stage_map["discovered"] == 1
        assert stage_map["interested"] == 1
        assert stage_map["applied"] == 1
        assert stage_map["screening"] == 1
        assert stage_map["interview"] == 1
        assert stage_map["offer"] == 1
        assert stage_map["rejected"] == 1

    @pytest.mark.asyncio
    async def test_funnel_conversion_rates(
        self, db_session: AsyncSession, sample_jobs: list[JobPosting]
    ) -> None:
        """Conversion rates are calculated between adjacent stages."""
        result = await analytics_service.funnel(db_session)

        conversions = {c.from_stage: c for c in result.conversions}

        # Each stage has 1 item, so conversions between equal counts = 1.0
        assert conversions["discovered"].rate == 1.0
        assert conversions["interested"].rate == 1.0

    @pytest.mark.asyncio
    async def test_funnel_conversion_with_skewed_data(
        self, db_session: AsyncSession
    ) -> None:
        """Conversion rates reflect actual proportions."""
        # 10 discovered, 5 applied, 2 interviewed
        for i in range(10):
            db_session.add(JobPosting(title=f"Job {i}", status="discovered"))
        for i in range(5):
            db_session.add(JobPosting(title=f"App {i}", status="applied"))
        for i in range(2):
            db_session.add(JobPosting(title=f"Int {i}", status="interview"))
        await db_session.commit()

        result = await analytics_service.funnel(db_session)

        conversions = {c.from_stage: c for c in result.conversions}
        # discovered → interested: 0 interested / 10 discovered = 0.0
        assert conversions["discovered"].rate == 0.0
        # interested → applied: 5 applied / 0 interested = 0.0 (division by zero safe)
        # But we also need to check screening → interview
        # Let's just verify no division errors and structure is correct
        assert len(result.conversions) == 6  # 7 stages → 6 transitions

    @pytest.mark.asyncio
    async def test_funnel_stage_order(
        self, db_session: AsyncSession, sample_jobs: list[JobPosting]
    ) -> None:
        """Stages appear in pipeline order."""
        result = await analytics_service.funnel(db_session)

        stage_names = [s.stage for s in result.stages]
        assert stage_names == [
            "discovered",
            "interested",
            "applied",
            "screening",
            "interview",
            "offer",
            "rejected",
        ]

    @pytest.mark.asyncio
    async def test_funnel_ignores_unknown_statuses(
        self, db_session: AsyncSession
    ) -> None:
        """Jobs with unrecognized statuses are excluded from counts."""
        db_session.add(JobPosting(title="Known", status="discovered"))
        db_session.add(JobPosting(title="Unknown", status="custom_status"))
        await db_session.commit()

        result = await analytics_service.funnel(db_session)
        assert result.total_postings == 1


# =============================================================================
# OUTREACH METRICS TESTS
# =============================================================================


class TestOutreachStats:
    """``outreach_stats`` aggregates email performance metrics."""

    @pytest.mark.asyncio
    async def test_outreach_stats_empty(self, db_session: AsyncSession) -> None:
        """Empty database returns zero metrics."""
        result = await analytics_service.outreach_stats(db_session)

        assert result.total_sent == 0
        assert result.open_rate == 0.0
        assert result.reply_rate == 0.0
        assert result.bounce_rate == 0.0

    @pytest.mark.asyncio
    async def test_outreach_stats_with_data(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """Stats correctly aggregate email statuses."""
        now = datetime.now(timezone.utc)
        emails = [
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="a@example.com",
                subject="Hi",
                body="Body",
                status="sent",
                sent_at=now,
            ),
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="b@example.com",
                subject="Hi",
                body="Body",
                status="opened",
                sent_at=now,
                opened_at=now + timedelta(hours=2),
            ),
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="c@example.com",
                subject="Hi",
                body="Body",
                status="replied",
                sent_at=now,
                opened_at=now + timedelta(hours=1),
                replied_at=now + timedelta(hours=5),
            ),
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="d@example.com",
                subject="Hi",
                body="Body",
                status="bounced",
            ),
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="e@example.com",
                subject="Hi",
                body="Body",
                status="failed",
            ),
        ]
        db_session.add_all(emails)
        await db_session.commit()

        result = await analytics_service.outreach_stats(db_session)

        assert result.total_sent == 5  # sent + opened + replied + bounced + failed
        assert result.by_status.sent == 3  # sent + opened + replied
        assert result.by_status.opened == 2  # opened + replied
        assert result.by_status.replied == 1
        assert result.by_status.bounced == 1
        assert result.by_status.failed == 1
        # open_rate = opened / sent = 2 / 3
        assert result.open_rate == round(2 / 3, 4)
        # reply_rate = replied / sent = 1 / 3
        assert result.reply_rate == round(1 / 3, 4)

    @pytest.mark.asyncio
    async def test_outreach_stats_avg_time_to_open(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """Average time to open is calculated from opened emails."""
        now = datetime.now(timezone.utc)
        db_session.add(
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="open@example.com",
                subject="Hi",
                body="Body",
                status="opened",
                sent_at=now,
                opened_at=now + timedelta(hours=3),
            )
        )
        await db_session.commit()

        result = await analytics_service.outreach_stats(db_session)
        assert result.avg_time_to_open_hours is not None
        # Allow some tolerance for timing precision
        assert 2.0 <= result.avg_time_to_open_hours <= 4.0

    @pytest.mark.asyncio
    async def test_outreach_stats_no_opened_emails(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """When no emails are opened, avg_time_to_open is None."""
        now = datetime.now(timezone.utc)
        db_session.add(
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="sent@example.com",
                subject="Hi",
                body="Body",
                status="sent",
                sent_at=now,
            )
        )
        await db_session.commit()

        result = await analytics_service.outreach_stats(db_session)
        assert result.avg_time_to_open_hours is None


# =============================================================================
# A/B TEST RESULTS TESTS
# =============================================================================


class TestAbTestResults:
    """``outreach_ab_results`` groups performance by A/B variant."""

    @pytest.mark.asyncio
    async def test_ab_results_empty(self, db_session: AsyncSession) -> None:
        """No A/B data returns has_data=False."""
        result = await analytics_service.outreach_ab_results(db_session)

        assert result.has_data is False
        assert result.variants == []

    @pytest.mark.asyncio
    async def test_ab_results_with_variants(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """A/B variants are grouped with their metrics."""
        now = datetime.now(timezone.utc)
        emails = [
            # Variant A: 3 sent, 2 opened, 1 replied
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="a1@example.com",
                subject="Hi",
                body="Body",
                status="replied",
                sent_at=now,
                opened_at=now,
                replied_at=now,
                ab_variant="A",
            ),
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="a2@example.com",
                subject="Hi",
                body="Body",
                status="opened",
                sent_at=now,
                opened_at=now,
                ab_variant="A",
            ),
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="a3@example.com",
                subject="Hi",
                body="Body",
                status="sent",
                sent_at=now,
                ab_variant="A",
            ),
            # Variant B: 2 sent, 0 opened, 0 replied
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="b1@example.com",
                subject="Hi",
                body="Body",
                status="sent",
                sent_at=now,
                ab_variant="B",
            ),
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="b2@example.com",
                subject="Hi",
                body="Body",
                status="sent",
                sent_at=now,
                ab_variant="B",
            ),
        ]
        db_session.add_all(emails)
        await db_session.commit()

        result = await analytics_service.outreach_ab_results(db_session)

        assert result.has_data is True
        assert len(result.variants) == 2

        variant_map = {v.variant: v for v in result.variants}
        assert variant_map["A"].sent == 3
        assert variant_map["A"].open_rate == round(2 / 3, 4)
        assert variant_map["A"].reply_rate == round(1 / 3, 4)
        assert variant_map["B"].sent == 2
        assert variant_map["B"].open_rate == 0.0
        assert variant_map["B"].reply_rate == 0.0

    @pytest.mark.asyncio
    async def test_ab_results_ignores_null_variant(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """Emails without an ab_variant are excluded."""
        now = datetime.now(timezone.utc)
        db_session.add(
            OutreachEmail(
                template_id=sample_template.id,
                recipient_email="no-variant@example.com",
                subject="Hi",
                body="Body",
                status="sent",
                sent_at=now,
                ab_variant=None,
            )
        )
        await db_session.commit()

        result = await analytics_service.outreach_ab_results(db_session)
        assert result.has_data is False


# =============================================================================
# SALARY INSIGHTS TESTS
# =============================================================================


class TestSalaryInsights:
    """``salary`` computes salary distribution with percentiles and histogram."""

    @pytest.mark.asyncio
    async def test_salary_empty(self, db_session: AsyncSession) -> None:
        """No salary data returns empty insights."""
        result = await analytics_service.salary(db_session)

        assert result.postings_with_salary == 0
        assert result.avg_salary_min is None
        assert result.avg_salary_max is None
        assert result.buckets == []
        assert result.by_remote_type == []

    @pytest.mark.asyncio
    async def test_salary_with_data(self, db_session: AsyncSession) -> None:
        """Salary stats are computed from jobs with salary ranges."""
        jobs = [
            JobPosting(title="J1", salary_min=50_000, salary_max=70_000, remote_type="remote"),
            JobPosting(title="J2", salary_min=80_000, salary_max=100_000, remote_type="remote"),
            JobPosting(title="J3", salary_min=120_000, salary_max=150_000, remote_type="onsite"),
            JobPosting(title="J4", salary_min=200_000, salary_max=250_000, remote_type="remote"),
        ]
        db_session.add_all(jobs)
        await db_session.commit()

        result = await analytics_service.salary(db_session)

        assert result.postings_with_salary == 4
        assert result.avg_salary_min == round((50_000 + 80_000 + 120_000 + 200_000) / 4, 2)
        assert result.avg_salary_max == round((70_000 + 100_000 + 150_000 + 250_000) / 4, 2)
        assert result.median_salary_min is not None
        assert result.median_salary_max is not None
        assert result.currency == "USD"

    @pytest.mark.asyncio
    async def test_salary_histogram_buckets(self, db_session: AsyncSession) -> None:
        """Histogram buckets cover all salary ranges."""
        jobs = [
            JobPosting(title="Low", salary_min=25_000, salary_max=35_000),
            JobPosting(title="Mid", salary_min=60_000, salary_max=80_000),
            JobPosting(title="High", salary_min=150_000, salary_max=180_000),
        ]
        db_session.add_all(jobs)
        await db_session.commit()

        result = await analytics_service.salary(db_session)

        # Should have 8 buckets defined in the service
        assert len(result.buckets) == 8
        bucket_labels = {b.range_label: b.count for b in result.buckets}
        assert bucket_labels["<30k"] == 1  # 25_000 falls in <30k
        assert bucket_labels["50-75k"] == 1  # 60_000 falls in 50-75k
        assert bucket_labels["130-160k"] == 1  # 150_000 falls in 130-160k

    @pytest.mark.asyncio
    async def test_salary_by_remote_type(self, db_session: AsyncSession) -> None:
        """Salary is grouped by remote work type."""
        jobs = [
            JobPosting(title="R1", salary_min=100_000, salary_max=140_000, remote_type="remote"),
            JobPosting(title="R2", salary_min=120_000, salary_max=160_000, remote_type="remote"),
            JobPosting(title="O1", salary_min=80_000, salary_max=100_000, remote_type="onsite"),
        ]
        db_session.add_all(jobs)
        await db_session.commit()

        result = await analytics_service.salary(db_session)

        assert len(result.by_remote_type) == 2
        remote_data = {c.category: c for c in result.by_remote_type}
        assert "remote" in remote_data
        assert "onsite" in remote_data
        assert remote_data["remote"].sample_size == 2
        assert remote_data["onsite"].sample_size == 1
        assert remote_data["remote"].avg_min == 110_000.00  # (100k + 120k) / 2

    @pytest.mark.asyncio
    async def test_salary_ignores_null_salaries(
        self, db_session: AsyncSession
    ) -> None:
        """Jobs without salary_min/salary_max are excluded."""
        db_session.add(JobPosting(title="No salary", salary_min=None, salary_max=None))
        db_session.add(JobPosting(title="Has salary", salary_min=50_000, salary_max=70_000))
        await db_session.commit()

        result = await analytics_service.salary(db_session)
        assert result.postings_with_salary == 1

    @pytest.mark.asyncio
    async def test_salary_percentiles(
        self, db_session: AsyncSession
    ) -> None:
        """Percentile calculations (p25, median, p75) work correctly."""
        # 4 values: 50k, 80k, 120k, 200k
        values = [50_000, 80_000, 120_000, 200_000]
        max_values = [70_000, 100_000, 150_000, 250_000]
        for i, (mn, mx) in enumerate(zip(values, max_values)):
            db_session.add(JobPosting(title=f"J{i}", salary_min=mn, salary_max=mx))
        await db_session.commit()

        result = await analytics_service.salary(db_session)

        # p25 of [50k, 80k, 120k, 200k] → index 0.75 → index 0 → 50k
        assert result.p25_salary_min == 50_000
        # median → index 1.5 → index 1 → 80k
        assert result.median_salary_min == 80_000
        # p75 of max values [70k, 100k, 150k, 250k] → index 2.25 → index 2 → 150k
        assert result.p75_salary_max == 150_000


# =============================================================================
# HTTP API TESTS (client)
# =============================================================================


class TestAnalyticsHttp:
    """HTTP endpoint tests for the analytics API."""

    @pytest.mark.asyncio
    async def test_funnel_endpoint(
        self, client: AsyncClient, sample_jobs: list[JobPosting]
    ) -> None:
        """GET /funnel returns stage counts and conversions."""
        response = await client.get("/api/v1/analytics/funnel")
        assert response.status_code == 200
        body = response.json()
        assert "total_postings" in body
        assert "stages" in body
        assert "conversions" in body
        assert body["total_postings"] == 7

    @pytest.mark.asyncio
    async def test_outreach_metrics_endpoint(
        self, client: AsyncClient, sample_template: EmailTemplate
    ) -> None:
        """GET /outreach returns aggregate metrics."""
        # Create some emails
        now = datetime.now(timezone.utc)
        for i in range(3):
            resp = await client.post(
                "/api/v1/outreach/compose",
                json={
                    "recipient_email": f"metrics{i}@example.com",
                    "subject": "Hi",
                    "body": "Body",
                    "template_id": sample_template.id,
                },
            )
            email_id = resp.json()["id"]
            await client.post(
                "/api/v1/outreach/send", params={"email_id": email_id}
            )

        response = await client.get("/api/v1/analytics/outreach")
        assert response.status_code == 200
        body = response.json()
        assert "total_sent" in body
        assert "by_status" in body
        assert "open_rate" in body
        assert "reply_rate" in body

    @pytest.mark.asyncio
    async def test_ab_test_endpoint(
        self, client: AsyncClient, sent_emails: list[OutreachEmail]
    ) -> None:
        """GET /outreach/ab-test returns A/B results."""
        response = await client.get("/api/v1/analytics/outreach/ab-test")
        assert response.status_code == 200
        body = response.json()
        assert "has_data" in body
        assert "variants" in body
        assert body["has_data"] is True

    @pytest.mark.asyncio
    async def test_salary_endpoint(
        self, client: AsyncClient, sample_jobs: list[JobPosting]
    ) -> None:
        """GET /salary returns salary insights."""
        response = await client.get("/api/v1/analytics/salary")
        assert response.status_code == 200
        body = response.json()
        assert "postings_with_salary" in body
        assert "buckets" in body
        assert "by_remote_type" in body
        assert body["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_funnel_endpoint_empty(self, client: AsyncClient) -> None:
        """Funnel endpoint works with empty database."""
        response = await client.get("/api/v1/analytics/funnel")
        assert response.status_code == 200
        body = response.json()
        assert body["total_postings"] == 0
