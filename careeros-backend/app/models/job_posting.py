"""JobPosting entity — discovered job opportunities."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import JSON, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.company import Company

RemoteType = Literal["onsite", "remote", "hybrid"]


class JobPosting(Base):
    __tablename__ = "job_postings"
    __table_args__ = (
        Index("ix_job_postings_portal", "portal_source", "portal_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1024), unique=True)
    salary_min: Mapped[int | None] = mapped_column()
    salary_max: Mapped[int | None] = mapped_column()
    currency: Mapped[str | None] = mapped_column(String(3), default="USD")
    location: Mapped[str | None] = mapped_column(String(200))
    remote_type: Mapped[RemoteType | None] = mapped_column(String(20))
    visa_sponsorship: Mapped[bool] = mapped_column(default=False)
    portal_source: Mapped[str | None] = mapped_column(String(50), index=True)
    portal_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="discovered", index=True)
    discovered_at: Mapped[datetime | None] = mapped_column()
    applied_at: Mapped[datetime | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Relationships
    company: Mapped["Company | None"] = relationship(back_populates="job_postings")
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job_posting", cascade="all, delete-orphan"
    )
