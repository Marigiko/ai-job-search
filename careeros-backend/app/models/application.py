"""Application entity — tracks a candidate's application to a job."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.job_posting import JobPosting
    from app.models.outreach_email import OutreachEmail

ApplicationStatus = Literal[
    "interested",
    "applied",
    "screening",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
]


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        # One application per job posting
        # (enforced in service layer for clearer error messages)
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        String(30), default="interested", index=True
    )
    applied_date: Mapped[date | None] = mapped_column(Date)
    follow_up_date: Mapped[date | None] = mapped_column(Date)
    cv_version: Mapped[str | None] = mapped_column(String(50))
    cover_letter_version: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column()

    # Relationships
    job_posting: Mapped["JobPosting"] = relationship(back_populates="applications")
    outreach_emails: Mapped[list["OutreachEmail"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
