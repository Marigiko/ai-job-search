"""Abstract base class for portal search plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from app.schemas.job import JobPostingCreate


class PortalPlugin(ABC):
    """Base interface for job portal integrations.

    Each plugin is self-contained: it knows its own API URL, how to fetch,
    how to filter client-side, and how to normalize raw payloads into the
    canonical ``JobPostingCreate`` schema used by the CareerOS database.
    """

    name: ClassVar[str]
    """Human-readable portal identifier (e.g. ``"remoteok"``). Used as the
    ``portal_source`` column and the registry lookup key."""

    base_url: ClassVar[str]
    """Public API base URL without query string."""

    @abstractmethod
    async def search(
        self,
        query: str | None = None,
        *,
        location: str | None = None,
        remote: bool | None = None,
        visa: bool | None = None,
        min_salary: int | None = None,
        jobage: int | None = None,
        limit: int = 50,
        page: int = 1,
        extra: dict[str, Any] | None = None,
    ) -> list[JobPostingCreate]:
        """Search the portal and return normalized job postings.

        Args:
            query: Free-text keyword (AND semantics across title/company/tags/description).
            location: Case-insensitive location substring filter.
            remote: When ``True``, only remote-friendly roles.
            visa: When ``True``, only roles hinting at visa/relocation.
            min_salary: Annual gross floor. Postings with a known max below
                this are dropped; unknown-salary postings are always kept.
            jobage: Maximum posting age in days.
            limit: Hard cap on results returned.
            page: 1-indexed start page for paginated feeds.
            extra: Plugin-specific escape hatch for forward-compatible params.

        Returns:
            A list of :class:`JobPostingCreate` ready for dedup + persistence.
        """
        ...

    @abstractmethod
    async def healthcheck(self) -> bool:
        """Verify the plugin endpoint is reachable and returns a valid shape."""
        ...
