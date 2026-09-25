"""OutreachEmail entity — sent or queued emails."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.email_event import EmailEvent
    from app.models.email_template import EmailTemplate

EmailStatus = Literal[
    "draft",
    "queued",
    "sent",
    "opened",
    "replied",
    "bounced",
    "failed",
]


class OutreachEmail(Base):
    __tablename__ = "outreach_emails"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("email_templates.id", ondelete="SET NULL")
    )
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[EmailStatus] = mapped_column(String(20), default="draft", index=True)
    sent_at: Mapped[datetime | None] = mapped_column()
    opened_at: Mapped[datetime | None] = mapped_column()
    replied_at: Mapped[datetime | None] = mapped_column()
    ab_variant: Mapped[str | None] = mapped_column(String(1))  # "A" or "B"

    # Relationships
    application: Mapped["Application | None"] = relationship(back_populates="outreach_emails")
    template: Mapped["EmailTemplate | None"] = relationship(back_populates="outreach_emails")
    events: Mapped[list["EmailEvent"]] = relationship(
        back_populates="outreach_email", cascade="all, delete-orphan"
    )
