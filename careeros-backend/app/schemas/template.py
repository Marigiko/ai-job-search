"""Email template schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EmailTemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    subject_template: str = Field(min_length=1, max_length=500)
    body_template: str = Field(min_length=1)
    language: str = Field(default="en", max_length=10)
    is_ab_test: bool = False
    ab_group_id: str | None = Field(default=None, max_length=100)
    ab_variant: str | None = Field(default=None, max_length=1)


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    subject_template: str | None = Field(default=None, min_length=1, max_length=500)
    body_template: str | None = None
    language: str | None = Field(default=None, max_length=10)
    is_ab_test: bool | None = None
    ab_group_id: str | None = Field(default=None, max_length=100)
    ab_variant: str | None = Field(default=None, max_length=1)


class EmailTemplateResponse(EmailTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usage_count: int
    reply_rate: float | None = None
