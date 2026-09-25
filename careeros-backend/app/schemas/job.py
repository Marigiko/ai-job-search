"""Job posting schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.job_posting import RemoteType


class JobPostingBase(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    url: HttpUrl | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default="USD", max_length=3)
    location: str | None = Field(default=None, max_length=200)
    remote_type: RemoteType | None = None
    visa_sponsorship: bool = False
    portal_source: str | None = Field(default=None, max_length=50)
    portal_id: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    raw_data: dict[str, Any] | None = None


class JobPostingCreate(JobPostingBase):
    company_id: int | None = None


class JobPostingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    url: HttpUrl | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=3)
    location: str | None = None
    remote_type: RemoteType | None = None
    visa_sponsorship: bool | None = None
    status: str | None = Field(default=None, max_length=30)
    notes: str | None = None


class JobPostingResponse(JobPostingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int | None = None
    status: str
    discovered_at: datetime | None = None
    applied_at: datetime | None = None
