"""Custom exception classes for the application."""

from __future__ import annotations


class CareerOSError(Exception):
    """Base exception for all CareerOS errors."""


class NotFoundError(CareerOSError):
    """Raised when a requested resource does not exist."""


class DuplicateError(CareerOSError):
    """Raised when a uniqueness constraint would be violated."""


class ValidationError(CareerOSError):
    """Raised when input validation fails beyond Pydantic schemas."""
