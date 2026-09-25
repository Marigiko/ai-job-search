"""EmailEvent entity — granular email lifecycle events."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.outreach_email import OutreachEmail


class EmailEvent(Base):
    __tablename__ = "email_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    outreach_email_id: Mapped[int] = mapped_column(
        ForeignKey("outreach_emails.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(nullable=False, index=True)

    # Relationships
    outreach_email: Mapped["OutreachEmail"] = relationship(back_populates="events")
