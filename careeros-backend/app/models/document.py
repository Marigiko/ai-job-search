"""Document entity — generated CVs and cover letters with version tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.job_posting import JobPosting

DocumentType = Literal["cv", "cover_letter"]
DocumentStatus = Literal["pending", "compiling", "ready", "failed"]


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index(
            "ix_documents_job_type_version",
            "job_posting_id",
            "document_type",
            "version",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_posting_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_postings.id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    variables_json: Mapped[str | None] = mapped_column(Text)
    tex_path: Mapped[str | None] = mapped_column(String(500))
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    compilation_log: Mapped[str | None] = mapped_column(Text)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[DocumentStatus] = mapped_column(
        String(20), default="pending", index=True
    )

    # Relationships
    job_posting: Mapped[JobPosting | None] = relationship()
    application: Mapped[Application | None] = relationship()
