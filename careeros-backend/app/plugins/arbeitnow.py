"""Arbeitnow portal plugin — Germany/EU-focused remote-friendly board.

API: https://www.arbeitnow.com/api/job-board-api?page=<n>  (no auth, no key).
Paginated feed (100/page) with no server-side keyword search. Pages carry
``links.next`` — when absent we've reached the end. Roles are remote-friendly
and many hint at visa/relocation support.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.logging import get_logger
from app.plugins.base import PortalPlugin
from app.plugins.registry import registry
from app.schemas.job import JobPostingCreate

logger = get_logger(__name__)

_API_URL = "https://www.arbeitnow.com/api/job-board-api"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_MAX_RETRIES = 6
_MAX_PAGES = 5


class _HtmlText:
    """Minimal HTML-to-text converter mirroring the TypeScript helpers."""

    _ENTITIES = {
        "amp": "&",
        "lt": "<",
        "gt": ">",
        "quot": '"',
        "apos": "'",
        "nbsp": " ",
    }

    @classmethod
    def decode(cls, text: str) -> str:
        def _numeric(match: re.Match[str]) -> str:
            body, base = (match.group(1) or match.group(3)), (10 if match.group(1) else 16)
            try:
                cp = int(body, base)
                return chr(cp) if 0 <= cp <= 0x10FFFF else ""
            except ValueError:
                return ""

        text = re.sub(r"&#(\d+);|&#[xX]([0-9a-fA-F]+);", _numeric, text)
        for name, char in cls._ENTITIES.items():
            text = text.replace(f"&{name};", char)
        return text

    @classmethod
    def convert(cls, html: str) -> str:
        text = re.sub(r"<\s*br\s*/?>", "\n", html, flags=re.IGNORECASE)
        text = re.sub(r"</(p|li|ul|ol|div|h\d)>", "\n", text, flags=re.IGNORECASE)
        text = cls.decode(re.sub(r"<[^>]+>", " ", text))
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        return re.sub(r"\n{3,}", "\n\n", text).strip()


def _iso_date(unix_seconds: float | None) -> str | None:
    if not unix_seconds:
        return None
    try:
        return datetime.fromtimestamp(unix_seconds, tz=timezone.utc).strftime("%Y-%m-%d")
    except (OSError, OverflowError, ValueError):
        return None


def _within_age(created_at: float | None, days: int | None) -> bool:
    if not days or days >= 9999:
        return True
    if created_at is None:
        return True
    age = (datetime.now(tz=timezone.utc).timestamp() - created_at) / 86400
    return age <= days


def _detect_visa(*, title: str, tags: list[str], description: str) -> bool:
    hay = " ".join([title, " ".join(tags), description]).lower()
    pattern = r"\b(relocation|relocate|umzug|visa|sponsor|sponsorship|work permit)\b"
    return bool(re.search(pattern, hay))


def _matches_query(
    *,
    query: str | None,
    title: str,
    company: str | None,
    tags: list[str],
    description: str | None,
) -> bool:
    if not query:
        return True
    hay = " ".join([title, company or "", " ".join(tags), description or ""]).lower()
    return all(term in hay for term in query.lower().split() if term)


class ArbeitnowPlugin(PortalPlugin):
    """Arbeitnow plugin — Germany/EU remote-friendly board."""

    name = "arbeitnow"
    base_url = _API_URL

    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=15.0,
                headers={
                    "User-Agent": _USER_AGENT,
                    "Accept": "application/json,text/plain,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                follow_redirects=True,
            )
        return self._client

    async def _fetch_page(self, page: int) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch a single page with exponential backoff.

        Returns ``(jobs, next_url)`` where ``next_url`` is ``None`` when the
        feed reports no further page.
        """
        client = await self._get_client()
        delay = 0.5
        for attempt in range(_MAX_RETRIES + 1):
            response = await client.get(_API_URL, params={"page": page})
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt == _MAX_RETRIES:
                    raise RuntimeError(
                        f"Arbeitnow request failed: {response.status_code} {response.reason_phrase}"
                    )
                await asyncio.sleep(delay + (attempt * 0.1))
                delay = min(delay * 2, 8.0)
                continue
            if response.status_code == 404:
                return [], None
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Arbeitnow API returned a non-object payload")
            jobs = data.get("data") or []
            if not isinstance(jobs, list):
                jobs = []
            next_url = (data.get("links") or {}).get("next")
            return jobs, next_url if isinstance(next_url, str) else None
        raise RuntimeError("Arbeitnow request failed after max retries")

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
        """Search Arbeitnow — pages forward from ``page``, stops at ``links.next`` end."""
        loc = location.lower() if location else None
        results: list[JobPostingCreate] = []

        for current_page in range(page, page + _MAX_PAGES):
            raw_jobs, next_url = await self._fetch_page(current_page)
            if not raw_jobs:
                break

            for raw in raw_jobs:
                if not isinstance(raw, dict):
                    continue
                title = (raw.get("title") or "").strip()
                if not title:
                    continue

                tags = [str(t) for t in (raw.get("tags") or []) if t]
                job_types = [str(t) for t in (raw.get("job_types") or []) if t]
                description = raw.get("description") or ""
                is_remote = bool(raw.get("remote"))

                if not _matches_query(
                    query=query,
                    title=title,
                    company=raw.get("company_name"),
                    tags=tags,
                    description=description,
                ):
                    continue
                if remote and not is_remote:
                    continue
                if not _within_age(raw.get("created_at"), jobage):
                    continue
                if loc:
                    raw_loc_str = (raw.get("location") or "").lower()
                    if loc not in raw_loc_str:
                        continue
                if visa and not _detect_visa(
                    title=title, tags=tags, description=description
                ):
                    continue

                raw_location = raw.get("location") or ("Remote" if is_remote else None)

                results.append(
                    JobPostingCreate(
                        title=title[:300],
                        description=_HtmlText.convert(description) if description else None,
                        url=raw.get("url") or "",
                        currency="EUR",  # default for Germany/EU
                        location=raw_location,
                        remote_type="remote" if is_remote else "onsite",
                        visa_sponsorship=bool(
                            visa
                            and _detect_visa(title=title, tags=tags, description=description)
                        ),
                        portal_source="arbeitnow",
                        portal_id=raw.get("slug"),
                        raw_data={
                            "tags": tags,
                            "job_types": job_types,
                            "created_at": raw.get("created_at"),
                        },
                    )
                )
                if len(results) >= limit:
                    break

            if len(results) >= limit:
                break
            if not next_url:
                break

        logger.info("Arbeitnow search returned %d results for query=%r", len(results), query)
        return results

    async def healthcheck(self) -> bool:
        """Return ``True`` if page 1 is reachable and contains jobs."""
        try:
            jobs, _ = await self._fetch_page(1)
            return len(jobs) > 0
        except Exception:
            logger.exception("Arbeitnow healthcheck failed")
            return False


registry.register(ArbeitnowPlugin())
