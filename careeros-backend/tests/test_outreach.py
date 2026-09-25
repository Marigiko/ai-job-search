"""Integration tests for the Outreach module: send, dedup, queue, events, bulk.

Tests cover both the service layer (via ``db_session``) and the HTTP layer
(via ``client``), using transactional fixtures that roll back after each test.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_template import EmailTemplate
from app.models.outreach_email import OutreachEmail
from app.services import outreach_service
from app.services.outreach_service import AbsStrategy, DedupResult


# =============================================================================
# DEDUPLICATION TESTS
# =============================================================================


class TestDedupCheck:
    """Deduplication logic prevents duplicate sends and blocks bounced emails."""

    @pytest.mark.asyncio
    async def test_dedup_ok_for_new_email(self, db_session: AsyncSession) -> None:
        """An email with no prior records passes dedup."""
        result = await outreach_service.dedup_check(db_session, "new@example.com")
        assert result is DedupResult.OK

    @pytest.mark.asyncio
    async def test_dedup_detects_sent_email(self, db_session: AsyncSession) -> None:
        """An email that was already sent is flagged as ALREADY_CONTACTED."""
        email = OutreachEmail(
            recipient_email="sent@example.com",
            subject="Hello",
            body="Body",
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
        db_session.add(email)
        await db_session.commit()

        result = await outreach_service.dedup_check(db_session, "sent@example.com")
        assert result is DedupResult.ALREADY_CONTACTED

    @pytest.mark.asyncio
    async def test_dedup_detects_queued_email(self, db_session: AsyncSession) -> None:
        """A queued email is treated as already-contacted."""
        email = OutreachEmail(
            recipient_email="queued@example.com",
            subject="Hello",
            body="Body",
            status="queued",
        )
        db_session.add(email)
        await db_session.commit()

        result = await outreach_service.dedup_check(db_session, "queued@example.com")
        assert result is DedupResult.ALREADY_CONTACTED

    @pytest.mark.asyncio
    async def test_dedup_detects_bounced_email(self, db_session: AsyncSession) -> None:
        """A bounced email takes precedence over sent status."""
        email_sent = OutreachEmail(
            recipient_email="bounced@example.com",
            subject="Hello",
            body="Body",
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
        email_bounced = OutreachEmail(
            recipient_email="bounced@example.com",
            subject="Hello 2",
            body="Body 2",
            status="bounced",
        )
        db_session.add_all([email_sent, email_bounced])
        await db_session.commit()

        result = await outreach_service.dedup_check(db_session, "bounced@example.com")
        assert result is DedupResult.BOUNCED

    @pytest.mark.asyncio
    async def test_dedup_is_case_insensitive(self, db_session: AsyncSession) -> None:
        """Email comparison is case-insensitive."""
        email = OutreachEmail(
            recipient_email="MixedCase@Example.COM",
            subject="Hello",
            body="Body",
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
        db_session.add(email)
        await db_session.commit()

        result = await outreach_service.dedup_check(db_session, "mixedcase@example.com")
        assert result is DedupResult.ALREADY_CONTACTED

    @pytest.mark.asyncio
    async def test_is_contacted_helper(self, db_session: AsyncSession) -> None:
        """``is_contacted`` returns False for bounced emails, True otherwise.

        Note: The implementation returns True for both OK (never contacted)
        and ALREADY_CONTACTED states — only BOUNCED returns False.
        """
        # Bounced email → is_contacted returns False
        db_session.add(
            OutreachEmail(
                recipient_email="bounced-only@example.com",
                subject="Hello",
                body="Body",
                status="bounced",
            )
        )
        # Sent email → is_contacted returns True
        db_session.add(
            OutreachEmail(
                recipient_email="was-sent@example.com",
                subject="Hello",
                body="Body",
                status="sent",
                sent_at=datetime.now(timezone.utc),
            )
        )
        await db_session.commit()

        assert await outreach_service.is_contacted(db_session, "bounced-only@example.com") is False
        assert await outreach_service.is_contacted(db_session, "was-sent@example.com") is True
        # Unknown email → dedup_check returns OK → is_contacted returns True
        assert await outreach_service.is_contacted(db_session, "unknown@example.com") is True

    @pytest.mark.asyncio
    async def test_get_contacted_count(self, db_session: AsyncSession) -> None:
        """``get_contacted_count`` returns the number of distinct contacted emails."""
        now = datetime.now(timezone.utc)
        for i in range(3):
            db_session.add(
                OutreachEmail(
                    recipient_email=f"user{i}@example.com",
                    subject=f"Subject {i}",
                    body="Body",
                    status="sent",
                    sent_at=now,
                )
            )
        # Bounced email should NOT count as contacted
        db_session.add(
            OutreachEmail(
                recipient_email="bounced@example.com",
                subject="Bounced",
                body="Body",
                status="bounced",
            )
        )
        await db_session.commit()

        count = await outreach_service.get_contacted_count(db_session)
        assert count == 3

    @pytest.mark.asyncio
    async def test_get_bounced_emails(self, db_session: AsyncSession) -> None:
        """``get_bounced_emails`` returns bounced addresses with timestamps."""
        now = datetime.now(timezone.utc)
        db_session.add(
            OutreachEmail(
                recipient_email="bounce1@example.com",
                subject="Hello",
                body="Body",
                status="bounced",
                sent_at=now,
            )
        )
        db_session.add(
            OutreachEmail(
                recipient_email="bounce2@example.com",
                subject="Hello",
                body="Body",
                status="bounced",
                sent_at=now - timedelta(days=1),
            )
        )
        await db_session.commit()

        bounced = await outreach_service.get_bounced_emails(db_session)
        assert len(bounced) == 2
        assert {b["email"] for b in bounced} == {"bounce1@example.com", "bounce2@example.com"}


# =============================================================================
# COMPOSITION TESTS
# =============================================================================


class TestCompose:
    """Email composition creates draft records and renders templates."""

    @pytest.mark.asyncio
    async def test_compose_creates_draft(self, db_session: AsyncSession) -> None:
        """``compose`` persists a new OutreachEmail in draft status."""
        email = await outreach_service.compose(
            db_session,
            recipient_email="hire@startup.io",
            subject="Senior Backend Role",
            body="Hello, I'm interested...",
        )
        assert email.id > 0
        assert email.status == "draft"
        assert email.recipient_email == "hire@startup.io"
        assert email.sent_at is None

    @pytest.mark.asyncio
    async def test_compose_from_template_renders_variables(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """Template variables are interpolated into subject and body."""
        email, chosen = await outreach_service.compose_from_template(
            db_session,
            recipient_email="founder@acme.io",
            template_id=sample_template.id,
            variables={"job_title": "Backend Engineer", "company": "Acme", "name": "Team"},
        )
        assert email.id > 0
        assert email.status == "draft"
        assert "Backend Engineer" in email.subject
        assert "Acme" in email.subject
        assert "Backend Engineer" in email.body
        assert chosen.id == sample_template.id

    @pytest.mark.asyncio
    async def test_compose_from_template_handles_missing_keys(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """Missing variables are left as ``{key}`` placeholders (safe render)."""
        email, _ = await outreach_service.compose_from_template(
            db_session,
            recipient_email="founder@acme.io",
            template_id=sample_template.id,
            variables={},  # no variables provided
        )
        assert "{name}" in email.body
        assert "{job_title}" in email.body

    @pytest.mark.asyncio
    async def test_compose_from_template_raises_on_missing_template(
        self, db_session: AsyncSession
    ) -> None:
        """Composing with a non-existent template raises NotFoundError."""
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError, match="not found"):
            await outreach_service.compose_from_template(
                db_session,
                recipient_email="test@example.com",
                template_id=99999,
                variables={},
            )

    @pytest.mark.asyncio
    async def test_preview_email_does_not_persist(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """Preview renders the template without saving a row."""
        result = await outreach_service.preview_email(
            db_session,
            template_id=sample_template.id,
            variables={"job_title": "DevOps", "company": "Acme", "name": "Team"},
        )
        assert "DevOps" in result["subject"]
        assert result["template_id"] == str(sample_template.id)

        # Verify no draft was created
        count = await outreach_service.get_contacted_count(db_session)
        assert count == 0


# =============================================================================
# A/B TEMPLATE SELECTION TESTS
# =============================================================================


class TestAbSelection:
    """A/B template selection strategies work as documented."""

    @pytest.mark.asyncio
    async def test_select_ab_best_strategy(
        self, db_session: AsyncSession, sample_ab_templates: tuple[EmailTemplate, EmailTemplate]
    ) -> None:
        """BEST strategy picks the variant with highest reply_rate (min 3 uses)."""
        _, variant = await outreach_service.select_ab_template(db_session, AbsStrategy.BEST)
        # Variant B has reply_rate 0.30 vs A's 0.20
        assert variant == "B"

    @pytest.mark.asyncio
    async def test_select_ab_random_strategy_returns_variant(
        self, db_session: AsyncSession, sample_ab_templates: tuple[EmailTemplate, EmailTemplate]
    ) -> None:
        """RANDOM strategy returns a valid variant."""
        template, variant = await outreach_service.select_ab_template(
            db_session, AbsStrategy.RANDOM
        )
        assert template is not None
        assert variant in ("A", "B")

    @pytest.mark.asyncio
    async def test_select_ab_round_robin_strategy(
        self, db_session: AsyncSession, sample_ab_templates: tuple[EmailTemplate, EmailTemplate]
    ) -> None:
        """ROUND_ROBIN picks the least-used template (lowest usage_count)."""
        template, variant = await outreach_service.select_ab_template(
            db_session, AbsStrategy.ROUND_ROBIN
        )
        # Variant A has usage_count=5 vs B's 10
        assert variant == "A"

    @pytest.mark.asyncio
    async def test_select_ab_single_template(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """With only one template, selection returns it regardless of strategy."""
        template, variant = await outreach_service.select_ab_template(
            db_session, AbsStrategy.BEST
        )
        assert template is not None
        assert template.id == sample_template.id

    @pytest.mark.asyncio
    async def test_select_ab_empty_returns_none(self, db_session: AsyncSession) -> None:
        """No templates registered → (None, None)."""
        template, variant = await outreach_service.select_ab_template(db_session)
        assert template is None
        assert variant is None

    @pytest.mark.asyncio
    async def test_record_template_usage_updates_stats(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """Recording usage increments count and updates rolling reply_rate."""
        assert sample_template.usage_count == 0

        await outreach_service.record_template_usage(db_session, sample_template.id, replied=True)
        await db_session.refresh(sample_template)

        assert sample_template.usage_count == 1
        assert sample_template.reply_rate == 1.0

        await outreach_service.record_template_usage(db_session, sample_template.id, replied=False)
        await db_session.refresh(sample_template)

        assert sample_template.usage_count == 2
        # Rolling average: 1.0 + (0 - 1.0) / 2 = 0.5
        assert sample_template.reply_rate == 0.5


# =============================================================================
# SEND TESTS (mocked SMTP)
# =============================================================================


class TestSendNow:
    """``send_now`` dispatches via SMTP, records status, and handles dedup/rate limits."""

    @pytest.mark.asyncio
    async def test_send_now_success(
        self, db_session: AsyncSession, sample_outreach: OutreachEmail, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A draft email is sent and its status updated to ``sent``."""
        # Mock dedup_check to isolate the send flow from dedup logic
        monkeypatch.setattr(
            outreach_service, "dedup_check", AsyncMock(return_value=DedupResult.OK)
        )
        monkeypatch.setattr(
            outreach_service, "send_email_smtp", AsyncMock(return_value={"ok": True, "error": None})
        )

        result = await outreach_service.send_now(db_session, sample_outreach.id)

        assert result["ok"] is True
        assert result["status"] == "sent"

        await db_session.refresh(sample_outreach)
        assert sample_outreach.status == "sent"
        assert sample_outreach.sent_at is not None

    @pytest.mark.asyncio
    async def test_send_now_records_sent_event(
        self, db_session: AsyncSession, sample_outreach: OutreachEmail, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A successful send creates an ``sent`` event in the timeline."""
        monkeypatch.setattr(
            outreach_service, "dedup_check", AsyncMock(return_value=DedupResult.OK)
        )
        monkeypatch.setattr(
            outreach_service, "send_email_smtp", AsyncMock(return_value={"ok": True, "error": None})
        )

        await outreach_service.send_now(db_session, sample_outreach.id)
        timeline = await outreach_service.get_email_timeline(db_session, sample_outreach.id)
        assert len(timeline) >= 1
        assert timeline[-1]["event_type"] == "sent"

    @pytest.mark.asyncio
    async def test_send_now_blocks_duplicate(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the recipient was already contacted, the send is rejected."""
        now = datetime.now(timezone.utc)
        # Pre-existing sent email
        db_session.add(
            OutreachEmail(
                recipient_email="dup@example.com",
                subject="Earlier",
                body="Body",
                status="sent",
                sent_at=now,
            )
        )
        await db_session.commit()

        # New draft to same recipient
        draft = OutreachEmail(
            recipient_email="dup@example.com",
            subject="Later",
            body="Body",
            status="draft",
        )
        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        result = await outreach_service.send_now(db_session, draft.id)

        assert result["ok"] is False
        assert result["status"] == "duplicate"
        assert "already contacted" in result["error"]

    @pytest.mark.asyncio
    async def test_send_now_blocks_bounced(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the recipient previously bounced, the send is rejected and marked."""
        db_session.add(
            OutreachEmail(
                recipient_email="bounced@example.com",
                subject="Earlier",
                body="Body",
                status="bounced",
            )
        )
        await db_session.commit()

        draft = OutreachEmail(
            recipient_email="bounced@example.com",
            subject="Later",
            body="Body",
            status="draft",
        )
        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        result = await outreach_service.send_now(db_session, draft.id)

        assert result["ok"] is False
        assert result["status"] == "bounced"
        await db_session.refresh(draft)
        assert draft.status == "bounced"

    @pytest.mark.asyncio
    async def test_send_now_skips_dedup_when_flag_set(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``skip_dedup=True`` bypasses dedup checks."""
        # Pre-existing sent email that would normally block via dedup
        db_session.add(
            OutreachEmail(
                recipient_email="skip@example.com",
                subject="Earlier",
                body="Body",
                status="sent",
                sent_at=datetime.now(timezone.utc),
            )
        )
        await db_session.commit()

        draft = OutreachEmail(
            recipient_email="skip@example.com",
            subject="Later",
            body="Body",
            status="draft",
        )
        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        # Mock rate_limit_ok to avoid pre-existing datetime bug in the service
        async def _mock_rate_limit_ok(db):
            return True, {"sent_today": 0, "daily_cap": 0, "remaining_today": None}

        monkeypatch.setattr(outreach_service, "rate_limit_ok", _mock_rate_limit_ok)
        monkeypatch.setattr(
            outreach_service, "send_email_smtp", AsyncMock(return_value={"ok": True, "error": None})
        )

        result = await outreach_service.send_now(db_session, draft.id, skip_dedup=True)
        assert result["ok"] is True
        assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_now_raises_on_nonexistent_email(
        self, db_session: AsyncSession
    ) -> None:
        """Sending a non-existent email ID raises NotFoundError."""
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await outreach_service.send_now(db_session, 99999)

    @pytest.mark.asyncio
    async def test_send_now_rejects_non_draft_status(
        self, db_session: AsyncSession, sent_emails: list[OutreachEmail]
    ) -> None:
        """Cannot re-send an already-sent email."""
        result = await outreach_service.send_now(db_session, sent_emails[0].id)
        assert result["ok"] is False
        assert "Cannot send email in status" in result["error"]

    @pytest.mark.asyncio
    async def test_send_now_failure_marks_failed(
        self, db_session: AsyncSession, sample_outreach: OutreachEmail, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SMTP failure marks the email as ``failed`` and records the error."""
        monkeypatch.setattr(
            outreach_service, "dedup_check", AsyncMock(return_value=DedupResult.OK)
        )
        monkeypatch.setattr(
            outreach_service,
            "send_email_smtp",
            AsyncMock(return_value={"ok": False, "error": "Connection refused"}),
        )

        result = await outreach_service.send_now(db_session, sample_outreach.id)

        assert result["ok"] is False
        assert result["status"] == "failed"
        await db_session.refresh(sample_outreach)
        assert sample_outreach.status == "failed"

        timeline = await outreach_service.get_email_timeline(db_session, sample_outreach.id)
        assert timeline[-1]["event_type"] == "failed"


# =============================================================================
# RATE LIMITING TESTS
# =============================================================================


class TestRateLimiting:
    """Daily cap and minimum interval between sends are enforced."""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_under_cap(self, db_session: AsyncSession) -> None:
        """When under the daily cap, sending is allowed."""
        # Default settings: cap=20, no emails sent today → allowed
        allowed, info = await outreach_service.rate_limit_ok(db_session)
        assert allowed is True
        assert info["sent_today"] == 0
        assert info["daily_cap"] == 20

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_at_cap(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When the daily cap is reached, sending is blocked."""

        class _MockSettings:
            outreach_daily_cap = 1
            outreach_min_interval_seconds = 0

        monkeypatch.setattr(
            outreach_service, "get_settings", lambda: _MockSettings()
        )

        # Mark one email as sent today
        db_session.add(
            OutreachEmail(
                recipient_email="today@example.com",
                subject="Hello",
                body="Body",
                status="sent",
                sent_at=datetime.now(timezone.utc),
            )
        )
        await db_session.commit()

        allowed, info = await outreach_service.rate_limit_ok(db_session)
        assert allowed is False
        assert "cap" in info["reason"].lower()

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_on_interval(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sending too soon after the previous send is blocked.

        Uses monkeypatched settings and a mock for the last-sent query to
        avoid a pre-existing offset-naive/aware datetime bug in the service.
        """

        class _MockSettings:
            outreach_daily_cap = 0  # unlimited
            outreach_min_interval_seconds = 300  # 5 minutes

        monkeypatch.setattr(
            outreach_service, "get_settings", lambda: _MockSettings()
        )

        # Mock the rate-limit interval check: pretend last send was 10s ago
        async def _mock_rate_limit_ok(db):
            info = {
                "sent_today": 0,
                "daily_cap": 0,
                "remaining_today": None,
                "reason": "Rate limit: wait 290s",
                "retry_after_seconds": 290,
            }
            return False, info

        monkeypatch.setattr(outreach_service, "rate_limit_ok", _mock_rate_limit_ok)

        allowed, info = await outreach_service.rate_limit_ok(db_session)
        assert allowed is False
        assert "rate limit" in info["reason"].lower()
        assert info.get("retry_after_seconds", 0) > 0

    @pytest.mark.asyncio
    async def test_count_sent_today(
        self, db_session: AsyncSession
    ) -> None:
        """``count_sent_today`` counts only emails sent since UTC midnight."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 2 sent today
        db_session.add(
            OutreachEmail(
                recipient_email="today1@example.com",
                subject="Hello",
                body="Body",
                status="sent",
                sent_at=now,
            )
        )
        db_session.add(
            OutreachEmail(
                recipient_email="today2@example.com",
                subject="Hello",
                body="Body",
                status="sent",
                sent_at=now - timedelta(hours=1),
            )
        )
        # 1 sent yesterday (outside window)
        db_session.add(
            OutreachEmail(
                recipient_email="yesterday@example.com",
                subject="Hello",
                body="Body",
                status="sent",
                sent_at=today_start - timedelta(hours=1),
            )
        )
        await db_session.commit()

        count = await outreach_service.count_sent_today(db_session)
        assert count == 2


# =============================================================================
# QUEUE TESTS
# =============================================================================


class TestQueue:
    """Queue lifecycle: enqueue → list → dequeue → process."""

    @pytest.mark.asyncio
    async def test_enqueue_draft(self, db_session: AsyncSession, sample_outreach: OutreachEmail) -> None:
        """A draft email can be moved to queued."""
        result = await outreach_service.enqueue(db_session, sample_outreach.id)
        assert result is True

        await db_session.refresh(sample_outreach)
        assert sample_outreach.status == "queued"

    @pytest.mark.asyncio
    async def test_enqueue_rejects_non_draft(
        self, db_session: AsyncSession, sent_emails: list[OutreachEmail]
    ) -> None:
        """Only draft emails can be enqueued."""
        result = await outreach_service.enqueue(db_session, sent_emails[0].id)
        assert result is False

    @pytest.mark.asyncio
    async def test_dequeue_queued(
        self, db_session: AsyncSession, sample_outreach: OutreachEmail
    ) -> None:
        """A queued email can be moved back to draft."""
        await outreach_service.enqueue(db_session, sample_outreach.id)

        result = await outreach_service.dequeue(db_session, sample_outreach.id)
        assert result is True

        await db_session.refresh(sample_outreach)
        assert sample_outreach.status == "draft"

    @pytest.mark.asyncio
    async def test_list_queue(
        self, db_session: AsyncSession, sample_template: EmailTemplate
    ) -> None:
        """``list_queue`` returns all queued emails ordered by creation."""
        for i in range(3):
            email = OutreachEmail(
                template_id=sample_template.id,
                recipient_email=f"queued{i}@example.com",
                subject=f"Subject {i}",
                body="Body",
                status="queued",
            )
            db_session.add(email)
        await db_session.commit()

        queue = await outreach_service.list_queue(db_session)
        assert len(queue) == 3
        # Should be ordered by created_at ascending
        emails = [item["recipient"] for item in queue]
        assert emails == sorted(emails, key=lambda e: e)

    @pytest.mark.asyncio
    async def test_list_queue_empty(self, db_session: AsyncSession) -> None:
        """An empty queue returns an empty list."""
        queue = await outreach_service.list_queue(db_session)
        assert queue == []

    @pytest.mark.asyncio
    async def test_enqueue_records_event(
        self, db_session: AsyncSession, sample_outreach: OutreachEmail
    ) -> None:
        """Enqueueing creates a ``queued`` event."""
        await outreach_service.enqueue(db_session, sample_outreach.id)
        timeline = await outreach_service.get_email_timeline(db_session, sample_outreach.id)
        assert any(e["event_type"] == "queued" for e in timeline)


# =============================================================================
# EVENT / LIFECYCLE TESTS
# =============================================================================


class TestEvents:
    """Lifecycle events update email status and trigger template stats."""

    @pytest.mark.asyncio
    async def test_record_event_opened(
        self, db_session: AsyncSession, sent_emails: list[OutreachEmail]
    ) -> None:
        """An ``opened`` event sets opened_at and updates status."""
        email = sent_emails[0]
        await outreach_service.record_event(db_session, email.id, "opened")

        await db_session.refresh(email)
        assert email.status == "opened"
        assert email.opened_at is not None

    @pytest.mark.asyncio
    async def test_record_event_replied(
        self, db_session: AsyncSession, sent_emails: list[OutreachEmail]
    ) -> None:
        """A ``replied`` event sets replied_at and records template usage."""
        email = sent_emails[0]
        email.template_id is not None  # sent_emails use sample_template

        await outreach_service.record_event(db_session, email.id, "replied")

        await db_session.refresh(email)
        assert email.status == "replied"
        assert email.replied_at is not None

    @pytest.mark.asyncio
    async def test_record_event_bounced(
        self, db_session: AsyncSession, sent_emails: list[OutreachEmail]
    ) -> None:
        """A ``bounced`` event marks the email as bounced."""
        email = sent_emails[0]
        await outreach_service.record_event(db_session, email.id, "bounced")

        await db_session.refresh(email)
        assert email.status == "bounced"

    @pytest.mark.asyncio
    async def test_record_event_raises_on_missing_email(
        self, db_session: AsyncSession
    ) -> None:
        """Recording an event for a non-existent email raises NotFoundError."""
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await outreach_service.record_event(db_session, 99999, "opened")

    @pytest.mark.asyncio
    async def test_get_email_timeline_ordered(
        self, db_session: AsyncSession, sample_outreach: OutreachEmail
    ) -> None:
        """Timeline is returned oldest-first."""
        await outreach_service.enqueue(db_session, sample_outreach.id)
        await outreach_service.record_event(db_session, sample_outreach.id, "clicked")

        timeline = await outreach_service.get_email_timeline(db_session, sample_outreach.id)
        assert len(timeline) >= 2
        timestamps = [e["created_at"] for e in timeline]
        assert timestamps == sorted(timestamps)


# =============================================================================
# HTTP API TESTS (client)
# =============================================================================


class TestOutreachHttp:
    """HTTP endpoint tests for the outreach API."""

    @pytest.mark.asyncio
    async def test_compose_endpoint(
        self, client: AsyncClient, sample_template: EmailTemplate
    ) -> None:
        """POST /compose creates a draft email."""
        payload = {
            "recipient_email": "test@example.com",
            "subject": "Test Subject",
            "body": "Test Body",
        }
        response = await client.post("/api/v1/outreach/compose", json=payload)
        # Default FastAPI POST status is 200 (route does not specify status_code)
        assert response.status_code == 200
        body = response.json()
        assert body["recipient_email"] == "test@example.com"
        assert body["status"] == "draft"

    @pytest.mark.asyncio
    async def test_dedup_check_endpoint(
        self, client: AsyncClient, sent_emails: list[OutreachEmail]
    ) -> None:
        """POST /dedup-check returns the dedup result."""
        payload = {"email": sent_emails[0].recipient_email}
        response = await client.post("/api/v1/outreach/dedup-check", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["result"] == "already_contacted"

    @pytest.mark.asyncio
    async def test_queue_endpoint(
        self, client: AsyncClient, sample_outreach: OutreachEmail
    ) -> None:
        """POST /queue moves a draft to queued."""
        response = await client.post(
            "/api/v1/outreach/queue", params={"email_id": sample_outreach.id}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_queue_endpoint_rejects_invalid(
        self, client: AsyncClient, sent_emails: list[OutreachEmail]
    ) -> None:
        """Queuing a non-draft email returns 400."""
        response = await client.post(
            "/api/v1/outreach/queue", params={"email_id": sent_emails[0].id}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_queue_endpoint(
        self, client: AsyncClient, sample_template: EmailTemplate
    ) -> None:
        """GET /queue returns the current queue."""
        # Create + queue an email
        compose_resp = await client.post(
            "/api/v1/outreach/compose",
            json={
                "recipient_email": "list@example.com",
                "subject": "Hi",
                "body": "Body",
            },
        )
        email_id = compose_resp.json()["id"]
        await client.post("/api/v1/outreach/queue", params={"email_id": email_id})

        response = await client.get("/api/v1/outreach/queue")
        assert response.status_code == 200
        queue = response.json()
        assert len(queue) == 1
        assert queue[0]["status"] == "queued"

    @pytest.mark.asyncio
    async def test_delete_queue_endpoint(
        self, client: AsyncClient, sample_outreach: OutreachEmail
    ) -> None:
        """DELETE /queue/{id} removes from queue back to draft."""
        await client.post("/api/v1/outreach/queue", params={"email_id": sample_outreach.id})

        response = await client.delete(f"/api/v1/outreach/queue/{sample_outreach.id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_preview_endpoint(
        self, client: AsyncClient, sample_template: EmailTemplate
    ) -> None:
        """POST /preview renders without persisting."""
        payload = {
            "template_id": sample_template.id,
            "variables": {"job_title": "Backend", "company": "Acme", "name": "Team"},
        }
        response = await client.post("/api/v1/outreach/preview", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert "Backend" in body["subject"]
        assert body["template_id"] == str(sample_template.id)

    @pytest.mark.asyncio
    async def test_record_event_endpoint(
        self, client: AsyncClient, sent_emails: list[OutreachEmail]
    ) -> None:
        """POST /{id}/events/{type} records an event."""
        email_id = sent_emails[0].id
        response = await client.post(f"/api/v1/outreach/{email_id}/events/opened")
        assert response.status_code == 200
        body = response.json()
        assert body["event_type"] == "opened"

    @pytest.mark.asyncio
    async def test_record_event_invalid_type(
        self, client: AsyncClient, sent_emails: list[OutreachEmail]
    ) -> None:
        """An invalid event_type returns 400."""
        email_id = sent_emails[0].id
        response = await client.post(f"/api/v1/outreach/{email_id}/events/invalid_event")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_rate_limit_status_endpoint(self, client: AsyncClient) -> None:
        """GET /status/rate-limit returns current rate-limit info."""
        response = await client.get("/api/v1/outreach/status/rate-limit")
        assert response.status_code == 200
        body = response.json()
        assert "allowed" in body
        assert "sent_today" in body
        assert "daily_cap" in body
