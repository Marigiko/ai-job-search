"""Integration tests for the Pipeline module: stage transitions, CRUD, Kanban.

Tests cover the service layer (via ``db_session``) and HTTP endpoints
(via ``client``), verifying stage ordering, transitions, and metrics.
"""

from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.job_posting import JobPosting
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.services import pipeline_service


# =============================================================================
# STAGE COUNTS / METRICS TESTS
# =============================================================================


class TestStageCounts:
    """``stage_counts`` returns correct counts per pipeline stage."""

    @pytest.mark.asyncio
    async def test_stage_counts_empty(self, db_session: AsyncSession) -> None:
        """Empty database returns zero for every stage."""
        counts = await pipeline_service.stage_counts(db_session)
        assert counts == {
            "discovered": 0,
            "interested": 0,
            "applied": 0,
            "screening": 0,
            "interview": 0,
            "offer": 0,
            "rejected": 0,
        }

    @pytest.mark.asyncio
    async def test_stage_counts_with_jobs(
        self, db_session: AsyncSession, sample_jobs: list[JobPosting]
    ) -> None:
        """Counts reflect jobs in each stage."""
        counts = await pipeline_service.stage_counts(db_session)
        # sample_jobs creates 1 job per stage (7 stages)
        assert counts["discovered"] == 1
        assert counts["interested"] == 1
        assert counts["applied"] == 1
        assert counts["screening"] == 1
        assert counts["interview"] == 1
        assert counts["offer"] == 1
        assert counts["rejected"] == 1

    @pytest.mark.asyncio
    async def test_stage_counts_multiple_per_stage(
        self, db_session: AsyncSession, sample_jobs: list[JobPosting]
    ) -> None:
        """Multiple jobs in the same stage are summed correctly."""
        # Add another discovered job
        extra = JobPosting(
            title="Extra Discovered",
            status="discovered",
        )
        db_session.add(extra)
        await db_session.commit()

        counts = await pipeline_service.stage_counts(db_session)
        assert counts["discovered"] == 2


# =============================================================================
# KANBAN GROUPS TESTS
# =============================================================================


class TestKanbanGroups:
    """``kanban_groups`` groups jobs by stage for the Kanban board."""

    @pytest.mark.asyncio
    async def test_kanban_groups_empty(self, db_session: AsyncSession) -> None:
        """Empty database returns empty lists for all stages."""
        groups = await pipeline_service.kanban_groups(db_session)
        for stage in pipeline_service.STAGE_ORDER:
            assert groups[stage] == []

    @pytest.mark.asyncio
    async def test_kanban_groups_with_jobs(
        self, db_session: AsyncSession, sample_jobs: list[JobPosting]
    ) -> None:
        """Jobs appear in their respective stage columns."""
        groups = await pipeline_service.kanban_groups(db_session)
        assert len(groups["discovered"]) == 1
        assert groups["discovered"][0]["title"] == "Backend Engineer"
        assert len(groups["offer"]) == 1
        assert groups["offer"][0]["title"] == "Staff Engineer"

    @pytest.mark.asyncio
    async def test_kanban_groups_default_stage(
        self, db_session: AsyncSession
    ) -> None:
        """Jobs with unrecognized status fall back to 'discovered'."""
        job = JobPosting(
            title="Weird Status Job",
            status="some_unknown_stage",
        )
        db_session.add(job)
        await db_session.commit()

        groups = await pipeline_service.kanban_groups(db_session)
        # Should be placed in 'discovered' as fallback
        assert len(groups["discovered"]) == 1


# =============================================================================
# APPLICATION CRUD TESTS
# =============================================================================


class TestApplicationCrud:
    """CRUD operations for Application records."""

    @pytest.mark.asyncio
    async def test_create_application(
        self, db_session: AsyncSession, sample_job: JobPosting
    ) -> None:
        """Creating an application persists a new row."""
        payload = ApplicationCreate(
            job_posting_id=sample_job.id,
            status="interested",
        )
        application = await pipeline_service.create_application(db_session, payload)

        assert application.id > 0
        assert application.job_posting_id == sample_job.id
        assert application.status == "interested"

    @pytest.mark.asyncio
    async def test_get_application(
        self, db_session: AsyncSession, sample_job: JobPosting
    ) -> None:
        """Fetching an application returns the correct record."""
        payload = ApplicationCreate(job_posting_id=sample_job.id, status="applied")
        created = await pipeline_service.create_application(db_session, payload)

        fetched = await pipeline_service.get_application(db_session, created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.status == "applied"

    @pytest.mark.asyncio
    async def test_get_application_not_found(self, db_session: AsyncSession) -> None:
        """Fetching a non-existent application returns None."""
        result = await pipeline_service.get_application(db_session, 99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_application_status(
        self, db_session: AsyncSession, sample_job: JobPosting
    ) -> None:
        """Status transitions update the application record."""
        payload = ApplicationCreate(job_posting_id=sample_job.id, status="interested")
        created = await pipeline_service.create_application(db_session, payload)

        # Transition: interested → applied
        update = ApplicationUpdate(status="applied", applied_date=date.today())
        updated = await pipeline_service.update_application(db_session, created.id, update)

        assert updated is not None
        assert updated.status == "applied"
        assert updated.applied_date == date.today()

    @pytest.mark.asyncio
    async def test_update_application_not_found(self, db_session: AsyncSession) -> None:
        """Updating a non-existent application returns None."""
        update = ApplicationUpdate(status="applied")
        result = await pipeline_service.update_application(db_session, 99999, update)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_application(
        self, db_session: AsyncSession, sample_job: JobPosting
    ) -> None:
        """Deleting an application removes it from the database."""
        payload = ApplicationCreate(job_posting_id=sample_job.id)
        created = await pipeline_service.create_application(db_session, payload)

        deleted = await pipeline_service.delete_application(db_session, created.id)
        assert deleted is True

        fetched = await pipeline_service.get_application(db_session, created.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_application_not_found(self, db_session: AsyncSession) -> None:
        """Deleting a non-existent application returns False."""
        result = await pipeline_service.delete_application(db_session, 99999)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_application_partial(
        self, db_session: AsyncSession, sample_job: JobPosting
    ) -> None:
        """Partial updates only modify provided fields."""
        payload = ApplicationCreate(
            job_posting_id=sample_job.id,
            status="interested",
            notes="Original notes",
        )
        created = await pipeline_service.create_application(db_session, payload)

        # Update only notes, not status
        update = ApplicationUpdate(notes="Updated notes")
        updated = await pipeline_service.update_application(db_session, created.id, update)

        assert updated is not None
        assert updated.status == "interested"  # unchanged
        assert updated.notes == "Updated notes"


# =============================================================================
# PAGINATION / LISTING TESTS
# =============================================================================


class TestApplicationListing:
    """``list_applications`` supports pagination and filtering."""

    @pytest.mark.asyncio
    async def test_list_applications_empty(self, db_session: AsyncSession) -> None:
        """Empty database returns no items."""
        result = await pipeline_service.list_applications(
            db_session, page=1, per_page=20, status_filter=None, job_posting_id=None
        )
        assert result.items == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_list_applications_pagination(
        self, db_session: AsyncSession, sample_job: JobPosting
    ) -> None:
        """Pagination returns the correct slice."""
        # Create 5 applications for the same job (one per job, so use different jobs)
        jobs = []
        for i in range(5):
            job = JobPosting(title=f"Job {i}", status="discovered")
            db_session.add(job)
            jobs.append(job)
        await db_session.commit()
        for job in jobs:
            await db_session.refresh(job)

        for job in jobs:
            db_session.add(Application(job_posting_id=job.id, status="interested"))
        await db_session.commit()

        # Page 1: 3 per page
        page1 = await pipeline_service.list_applications(
            db_session, page=1, per_page=3, status_filter=None, job_posting_id=None
        )
        assert len(page1.items) == 3
        assert page1.total == 5

        # Page 2: remaining 2
        page2 = await pipeline_service.list_applications(
            db_session, page=2, per_page=3, status_filter=None, job_posting_id=None
        )
        assert len(page2.items) == 2

    @pytest.mark.asyncio
    async def test_list_applications_filter_by_status(
        self, db_session: AsyncSession
    ) -> None:
        """Status filter returns only matching applications."""
        # Create actual job postings to satisfy FK constraints
        jobs = []
        for i in range(5):
            job = JobPosting(title=f"Filter Job {i}", status="discovered")
            db_session.add(job)
            jobs.append(job)
        await db_session.commit()
        for job in jobs:
            await db_session.refresh(job)

        for job in jobs[:3]:
            db_session.add(Application(job_posting_id=job.id, status="applied"))
        for job in jobs[3:]:
            db_session.add(Application(job_posting_id=job.id, status="interested"))
        await db_session.commit()

        result = await pipeline_service.list_applications(
            db_session, page=1, per_page=20, status_filter="applied", job_posting_id=None
        )
        assert result.total == 3
        assert all(a.status == "applied" for a in result.items)


# =============================================================================
# STAGE TRANSITION TESTS
# =============================================================================


class TestStageTransitions:
    """Application stage transitions follow the pipeline workflow."""

    @pytest.mark.asyncio
    async def test_full_pipeline_forward(
        self, db_session: AsyncSession, sample_job: JobPosting
    ) -> None:
        """An application can advance through every stage in order."""
        payload = ApplicationCreate(job_posting_id=sample_job.id, status="interested")
        app = await pipeline_service.create_application(db_session, payload)

        transitions: list[tuple[ApplicationStatus, ApplicationStatus]] = [
            ("interested", "applied"),
            ("applied", "screening"),
            ("screening", "interview"),
            ("interview", "offer"),
        ]
        for _from, to in transitions:
            update = ApplicationUpdate(status=to)
            app = await pipeline_service.update_application(db_session, app.id, update)
            assert app is not None
            assert app.status == to

    @pytest.mark.asyncio
    async def test_rejection_from_any_stage(
        self, db_session: AsyncSession, sample_job: JobPosting
    ) -> None:
        """An application can be rejected from the interview stage."""
        payload = ApplicationCreate(job_posting_id=sample_job.id, status="interested")
        app = await pipeline_service.create_application(db_session, payload)

        # Move to interview
        for stage in ("applied", "screening", "interview"):
            update = ApplicationUpdate(status=stage)
            app = await pipeline_service.update_application(db_session, app.id, update)

        # Reject
        update = ApplicationUpdate(status="rejected")
        app = await pipeline_service.update_application(db_session, app.id, update)
        assert app is not None
        assert app.status == "rejected"

    @pytest.mark.asyncio
    async def test_withdrawal(
        self, db_session: AsyncSession, sample_job: JobPosting
    ) -> None:
        """An application can be withdrawn."""
        payload = ApplicationCreate(job_posting_id=sample_job.id, status="applied")
        app = await pipeline_service.create_application(db_session, payload)

        update = ApplicationUpdate(status="withdrawn")
        app = await pipeline_service.update_application(db_session, app.id, update)
        assert app is not None
        assert app.status == "withdrawn"


# =============================================================================
# HTTP API TESTS (client)
# =============================================================================


class TestPipelineHttp:
    """HTTP endpoint tests for the pipeline API."""

    @pytest.mark.asyncio
    async def test_pipeline_counts_endpoint(
        self, client: AsyncClient, sample_jobs: list[JobPosting]
    ) -> None:
        """GET /counts returns stage counts."""
        response = await client.get("/api/v1/pipeline/counts")
        assert response.status_code == 200
        body = response.json()
        assert "stages" in body
        assert body["stages"]["discovered"] == 1

    @pytest.mark.asyncio
    async def test_kanban_endpoint(
        self, client: AsyncClient, sample_jobs: list[JobPosting]
    ) -> None:
        """GET /kanban returns jobs grouped by stage."""
        response = await client.get("/api/v1/pipeline/kanban")
        assert response.status_code == 200
        body = response.json()
        assert "stages" in body
        # Jobs without applications default to "discovered"
        assert len(body["stages"]["discovered"]) >= 1

    @pytest.mark.asyncio
    async def test_create_application_endpoint(
        self, client: AsyncClient, sample_job: JobPosting
    ) -> None:
        """POST /applications creates a new application."""
        payload = {
            "job_posting_id": sample_job.id,
            "status": "interested",
        }
        response = await client.post("/api/v1/pipeline/applications", json=payload)
        assert response.status_code == 201
        body = response.json()
        assert body["job_posting_id"] == sample_job.id
        assert body["status"] == "interested"

    @pytest.mark.asyncio
    async def test_get_application_endpoint(
        self, client: AsyncClient, sample_job: JobPosting
    ) -> None:
        """GET /applications/{id} returns the application."""
        # Create first
        payload = {"job_posting_id": sample_job.id, "status": "applied"}
        create_resp = await client.post("/api/v1/pipeline/applications", json=payload)
        app_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/pipeline/applications/{app_id}")
        assert response.status_code == 200
        assert response.json()["id"] == app_id

    @pytest.mark.asyncio
    async def test_get_application_not_found(self, client: AsyncClient) -> None:
        """GET /applications/{id} returns 404 for missing ID."""
        response = await client.get("/api/v1/pipeline/applications/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_application_endpoint(
        self, client: AsyncClient, sample_job: JobPosting
    ) -> None:
        """PATCH /applications/{id} updates the application."""
        payload = {"job_posting_id": sample_job.id, "status": "interested"}
        create_resp = await client.post("/api/v1/pipeline/applications", json=payload)
        app_id = create_resp.json()["id"]

        update_payload = {"status": "applied"}
        response = await client.patch(
            f"/api/v1/pipeline/applications/{app_id}", json=update_payload
        )
        assert response.status_code == 200
        assert response.json()["status"] == "applied"

    @pytest.mark.asyncio
    async def test_update_application_not_found(self, client: AsyncClient) -> None:
        """PATCH /applications/{id} returns 404 for missing ID."""
        response = await client.patch(
            "/api/v1/pipeline/applications/99999", json={"status": "applied"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_application_endpoint(
        self, client: AsyncClient, sample_job: JobPosting
    ) -> None:
        """DELETE /applications/{id} removes the application."""
        payload = {"job_posting_id": sample_job.id}
        create_resp = await client.post("/api/v1/pipeline/applications", json=payload)
        app_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/pipeline/applications/{app_id}")
        assert response.status_code == 204

        # Confirm deleted
        get_resp = await client.get(f"/api/v1/pipeline/applications/{app_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_applications_endpoint(
        self, client: AsyncClient, sample_job: JobPosting
    ) -> None:
        """GET /applications returns a paginated list."""
        # Create a few
        for i in range(3):
            job_resp = await client.post(
                "/api/v1/jobs",
                json={"title": f"List Job {i}"},
            )
            job_id = job_resp.json()["id"]
            await client.post(
                "/api/v1/pipeline/applications",
                json={"job_posting_id": job_id, "status": "interested"},
            )

        response = await client.get("/api/v1/pipeline/applications?per_page=2")
        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 2
        assert body["meta"]["total"] == 3

    @pytest.mark.asyncio
    async def test_list_applications_filter_by_status(
        self, client: AsyncClient, sample_job: JobPosting
    ) -> None:
        """Status filter narrows results."""
        # Create jobs + applications
        for i in range(2):
            job_resp = await client.post(
                "/api/v1/jobs",
                json={"title": f"Filter Job {i}"},
            )
            job_id = job_resp.json()["id"]
            await client.post(
                "/api/v1/pipeline/applications",
                json={"job_posting_id": job_id, "status": "applied" if i == 0 else "interested"},
            )

        response = await client.get(
            "/api/v1/pipeline/applications?status=applied"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["status"] == "applied"
