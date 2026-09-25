"""Document schemas — CV/CL generation, versioning, download."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentStatus, DocumentType


class DocumentGenerateRequest(BaseModel):
    """Request payload to generate a new CV or cover letter."""

    job_posting_id: int | None = None
    application_id: int | None = None
    company_id: int | None = None
    document_type: DocumentType
    template_name: str = Field(default="default", min_length=1, max_length=100)
    variables: dict[str, str] = Field(default_factory=dict)
    notes: str | None = None


class DocumentVersionResponse(BaseModel):
    """A single document version entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    document_type: DocumentType
    version: int
    template_name: str
    status: DocumentStatus
    pdf_path: str | None = None
    file_size_bytes: int | None = None
    created_at: datetime


class DocumentResponse(BaseModel):
    """Full document detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_posting_id: int | None = None
    application_id: int | None = None
    document_type: DocumentType
    version: int
    template_name: str
    variables_json: str | None = None
    tex_path: str | None = None
    pdf_path: str | None = None
    compilation_log: str | None = None
    file_size_bytes: int | None = None
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DocumentVersionsList(BaseModel):
    """List of all versions for a given document type + job."""

    job_posting_id: int
    document_type: DocumentType
    versions: list[DocumentVersionResponse]


class DocumentGenerateResponse(BaseModel):
    """Returned immediately after kicking off generation."""

    id: int
    status: DocumentStatus
    message: str


class DocumentListItem(BaseModel):
    """A single document entry in the list view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_posting_id: int | None = None
    company_id: int | None = None
    document_type: DocumentType
    version: int = 1
    status: DocumentStatus
    file_path: str | None = None
    file_size: int | None = None
    created_at: str | None = None
    job_title: str | None = None
    company_name: str | None = None


class DocumentCompileResult(BaseModel):
    """Internal result from the LaTeX compilation step."""

    success: bool
    pdf_path: str | None = None
    log: str | None = None
    file_size_bytes: int | None = None


class DocumentPreviewResponse(BaseModel):
    """Metadata for PDF preview."""

    document_id: int
    preview_url: str
    download_url: str
    status: DocumentStatus


class DocumentDownloadResponse(BaseModel):
    """Download link for a generated PDF."""

    document_id: int
    download_url: str
    filename: str
