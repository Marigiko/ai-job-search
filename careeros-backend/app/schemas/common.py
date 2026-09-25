"""Shared schema helpers."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""

    data: list[T]
    meta: PaginationMeta


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str

    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok", "version": "0.1.0"}})


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    detail: str | None = None
