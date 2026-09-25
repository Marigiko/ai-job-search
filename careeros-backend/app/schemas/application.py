"""Application schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import ApplicationStatus


class ApplicationBase(BaseModel):
    status: ApplicationStatus = "interested"
    applied_date: date | None = None
    follow_up_date: date | None = None
    cv_version: str | None = Field(default=None, max_length=50)
    cover_letter_version: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class ApplicationCreate(ApplicationBase):
    job_posting_id: int


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    applied_date: date | None = None
    follow_up_date: date | None = None
    cv_version: str | None = Field(default=None, max_length=50)
    cover_letter_version: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class ApplicationResponse(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_posting_id: int


class KanbanItem(BaseModel):
    """A job card displayed on the Kanban board."""

    job_id: int
    job_title: str
    company_name: str | None
    application_id: int | None
    status: str
    applied_date: date | None


class PipelineCountsResponse(BaseModel):
    """Count of applications per pipeline stage."""

    stages: dict[str, int]


class KanbanResponse(BaseModel):
    """Kanban board grouped by stage."""

    stages: dict[str, list[KanbanItem]]
