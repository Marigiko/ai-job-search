"""RemoteOK portal plugin — remote-only job board with annual-USD salaries.

API: https://remoteok.com/api  (no auth, no key).
The response is an array whose first element is a legal/metadata header
(ignored). Every listing is remote and many carry ``salary_min``/``salary_max``
annual-USD bands.
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

_API_URL = "https://remoteok.com/api"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_MAX_RETRIES = 6


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


def _nz(value: float | int | None) -> int | None:
    """Return ``value`` as int when strictly positive, else ``None``."""
    return int(value) if value and value > 0 else None


def _iso_date(*, date_str: str | None, epoch: float | None) -> str | None:
    """Prefer ISO ``date`` string, fall back to epoch seconds."""
    if date_str and re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        return date_str[:10]
    if epoch:
        try:
            return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            return None
    return None


def _detect_visa(*, position: str, tags: list[str], description: str) -> bool:
    hay = " ".join([position, *tags, description]).lower()
    return bool(re.search(r"\b(relocation|relocate|visa|sponsor|sponsorship|work permit)\b", hay))


def _matches_query(
    *,
    query: str | None,
    position: str,
    company: str | None,
    tags: list[str],
    description: str | None,
) -> bool:
    if not query:
        return True
    hay = " ".join([position, company or "", " ".join(tags), description or ""]).lower()
    return all(term in hay for term in query.lower().split() if term)


def _within_age(*, epoch: float | None, date_str: str | None, days: int | None) -> bool:
    if not days or days >= 9999:
        return True
    if epoch is not None:
        age = (datetime.now(tz=timezone.utc).timestamp() - epoch) / 86400
        return age <= days
    if date_str:
        try:
            published = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            age = (datetime.now(tz=timezone.utc) - published).days
            return age <= days
        except (ValueError, TypeError):
            return True
    return True


class RemoteOkPlugin(PortalPlugin):
    """RemoteOK plugin — every listing is remote, annual-USD salaries."""

    name = "remoteok"
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

    async def _fetch(self) -> list[dict[str, Any]]:
        """Fetch the full feed with exponential backoff on 429/5xx."""
        client = await self._get_client()
        delay = 0.5
        for attempt in range(_MAX_RETRIES + 1):
            response = await client.get(_API_URL)
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt == _MAX_RETRIES:
                    raise RuntimeError(
                        f"RemoteOK request failed: {response.status_code} {response.reason_phrase}"
                    )
                await asyncio.sleep(delay + (attempt * 0.1))
                delay = min(delay * 2, 8.0)
                continue
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("RemoteOK API returned a non-array payload")
            # First element is the legal/metadata header — skip it.
            return [item for item in data[1:] if isinstance(item, dict) and "position" in item]
        raise RuntimeError("RemoteOK request failed after max retries")

    async def search(
        self,
        query: str | None = None,
        *,
        location: str | None = None,
        remote: bool | None = None,  # all RemoteOK listings are remote
        visa: bool | None = None,
        min_salary: int | None = None,
        jobage: int | None = None,
        limit: int = 50,
        page: int = 1,
        extra: dict[str, Any] | None = None,
    ) -> list[JobPostingCreate]:
        """Search RemoteOK. ``page`` is unused — the feed is a single page."""
        raw_jobs = await self._fetch()
        loc = location.lower() if location else None
        results: list[JobPostingCreate] = []

        for raw in raw_jobs:
            position = (raw.get("position") or "").strip()
            if not position:
                continue
            company = raw.get("company") or None
            tags = [str(t) for t in (raw.get("tags") or []) if t]
            description = raw.get("description") or ""

            if not _matches_query(
                query=query,
                position=position,
                company=company,
                tags=tags,
                description=description,
            ):
                continue
            if not _within_age(
                epoch=raw.get("epoch"),
                date_str=raw.get("date"),
                days=jobage,
            ):
                continue
            if loc:
                raw_location = (raw.get("location") or "").lower()
                if loc not in raw_location:
                    continue

            salary_max = _nz(raw.get("salary_max"))
            if visa and not _detect_visa(
                position=position, tags=tags, description=description
            ):
                continue
            # Salary floor: drop only jobs whose KNOWN max is below the floor.
            if min_salary and salary_max is not None and salary_max < min_salary:
                continue

            url = (
                raw.get("url")
                or (f"https://remoteok.com/remote-jobs/{raw['slug']}" if raw.get("slug") else "")
                or ""
            )

            results.append(
                JobPostingCreate(
                    title=position[:300],
                    description=_HtmlText.convert(description) if description else None,
                    url=url if url else None,
                    salary_min=_nz(raw.get("salary_min")),
                    salary_max=salary_max,
                    currency="USD",
                    location=raw.get("location") or "Remote",
                    remote_type="remote",
                    visa_sponsorship=bool(
                        visa
                        and _detect_visa(position=position, tags=tags, description=description)
                    ),
                    portal_source="remoteok",
                    portal_id=str(raw.get("id") or raw.get("slug")),
                    raw_data={
                        "tags": tags,
                        "apply_url": raw.get("apply_url"),
                        "epoch": raw.get("epoch"),
                    },
                )
            )
            if len(results) >= limit:
                break

        logger.info("RemoteOK search returned %d results for query=%r", len(results), query)
        return results

    async def healthcheck(self) -> bool:
        """Return ``True`` if the feed is reachable and contains jobs."""
        try:
            jobs = await self._fetch()
            return len(jobs) > 0
        except Exception:
            logger.exception("RemoteOK healthcheck failed")
            return False


registry.register(RemoteOkPlugin())
