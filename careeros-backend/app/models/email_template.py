"""EmailTemplate entity — reusable outreach email templates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.outreach_email import OutreachEmail


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject_template: Mapped[str] = mapped_column(String(500), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    is_ab_test: Mapped[bool] = mapped_column(Boolean, default=False)
    ab_group_id: Mapped[str | None] = mapped_column(String(100), index=True)
    ab_variant: Mapped[str | None] = mapped_column(String(1))  # "A" or "B"
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_rate: Mapped[float | None] = mapped_column(Float)

    # Relationships
    outreach_emails: Mapped[list["OutreachEmail"]] = relationship(
        back_populates="template"
    )
