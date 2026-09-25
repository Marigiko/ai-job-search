"""Pydantic request/response schemas."""

from app.schemas.document import (
    DocumentGenerateRequest,
    DocumentResponse,
    DocumentVersionsList,
)

__all__ = [
    "DocumentGenerateRequest",
    "DocumentResponse",
    "DocumentVersionsList",
]
