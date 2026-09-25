"""Landing.jobs portal plugin — EU-focused tech board with relocation/visa flags.

API: https://landing.jobs/api/v1/jobs  (no auth, no key).
Paginated feed (100/page) with no server-side keyword search. Many roles
carry ``relocation_paid`` (surfaced as ``visa: "relocation"``). Salaries
are annual gross in the posting's currency (mostly EUR).
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

_API_URL = "https://landing.jobs/api/v1/jobs"
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


def _nz(value: float | int | None) -> int | None:
    return int(value) if value and value > 0 else None


def _iso_date(published: str | None) -> str | None:
    if not published:
        return None
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _within_age(published: str | None, days: int | None) -> bool:
    if not days or days >= 9999:
        return True
    if not published:
        return True
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        return (datetime.now(tz=timezone.utc) - dt).days <= days
    except (ValueError, TypeError):
        return True


def _company_from_url(url: str | None) -> str | None:
    """Company is not an API field — derive from the ``/at/<company>/`` slug."""
    if not url:
        return None
    match = re.search(r"/at/([^/]+)/", url)
    if not match:
        return None
    return " ".join(
        w.capitalize() for w in match.group(1).split("-") if w
    )


def _detect_visa(
    *,
    relocation_paid: bool,
    title: str,
    description: str | None,
    perks: str | None,
    tags: list[str],
) -> bool:
    if relocation_paid:
        return True
    hay = " ".join([title, description or "", perks or "", " ".join(tags)]).lower()
    return bool(re.search(r"\b(relocation|relocate|visa|sponsor|sponsorship|work permit)\b", hay))


def _location_str(*, locations: list[dict[str, str]] | None, is_remote: bool) -> str | None:
    if locations:
        parts = [
            ", ".join(filter(None, (loc.get("city"), loc.get("country_code"))))
            for loc in locations
        ]
        parts = [p for p in parts if p]
        if parts:
            return " | ".join(parts)
    return "Remote" if is_remote else None


def _matches_query(
    *,
    query: str | None,
    title: str,
    tags: list[str],
    requirements: str | None,
    description: str | None,
) -> bool:
    if not query:
        return True
    hay = " ".join([title, " ".join(tags), requirements or "", description or ""]).lower()
    return all(term in hay for term in query.lower().split() if term)


class LandingJobsPlugin(PortalPlugin):
    """Landing.jobs plugin — EU tech roles, relocation/visa friendly."""

    name = "landingjobs"
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

    async def _fetch_page(self, page: int) -> list[dict[str, Any]]:
        """Fetch a single page with exponential backoff on 429/5xx."""
        client = await self._get_client()
        delay = 0.5
        for attempt in range(_MAX_RETRIES + 1):
            response = await client.get(_API_URL, params={"page": page})
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt == _MAX_RETRIES:
                    msg = (
                        f"Landing.jobs request failed: "
                        f"{response.status_code} {response.reason_phrase}"
                    )
                    raise RuntimeError(msg)
                await asyncio.sleep(delay + (attempt * 0.1))
                delay = min(delay * 2, 8.0)
                continue
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("Landing.jobs API returned a non-array payload")
            return data
        raise RuntimeError("Landing.jobs request failed after max retries")

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
        """Search Landing.jobs — pages forward from ``page``, filters client-side."""
        loc = location.lower() if location else None
        results: list[JobPostingCreate] = []

        for current_page in range(page, page + _MAX_PAGES):
            raw_jobs = await self._fetch_page(current_page)
            if not raw_jobs:
                break

            for raw in raw_jobs:
                if not isinstance(raw, dict):
                    continue
                title = (raw.get("title") or "").strip()
                if not title:
                    continue

                tags = [str(t) for t in (raw.get("tags") or []) if t]
                is_remote = bool(raw.get("remote"))
                relocation_paid = bool(raw.get("relocation_paid"))

                if not _matches_query(
                    query=query,
                    title=title,
                    tags=tags,
                    requirements=raw.get("main_requirements"),
                    description=raw.get("role_description"),
                ):
                    continue
                if remote and not is_remote:
                    continue
                if not _within_age(raw.get("published_at"), jobage):
                    continue

                raw_location = _location_str(
                    locations=raw.get("locations"),
                    is_remote=is_remote,
                )
                if loc:
                    raw_loc_str = (raw_location or "").lower()
                    if loc not in raw_loc_str:
                        continue

                salary_high = _nz(raw.get("gross_salary_high"))
                if visa and not _detect_visa(
                    relocation_paid=relocation_paid,
                    title=title,
                    description=raw.get("role_description"),
                    perks=raw.get("perks"),
                    tags=tags,
                ):
                    continue
                # Salary floor: drop only jobs whose KNOWN max is below the floor.
                if min_salary and salary_high is not None and salary_high < min_salary:
                    continue

                url = raw.get("url") or ""
                salary_low = _nz(raw.get("gross_salary_low"))

                parts: list[str] = []
                if raw.get("role_description"):
                    parts.append(_HtmlText.convert(raw["role_description"]))
                if raw.get("main_requirements"):
                    parts.append("Requirements:\n" + _HtmlText.convert(raw["main_requirements"]))
                if raw.get("nice_to_have"):
                    parts.append("Nice to have:\n" + _HtmlText.convert(raw["nice_to_have"]))
                if raw.get("perks"):
                    parts.append("Perks:\n" + _HtmlText.convert(raw["perks"]))

                results.append(
                    JobPostingCreate(
                        title=title[:300],
                        description="\n\n".join(parts) if parts else None,
                        url=url if url else None,
                        salary_min=salary_low,
                        salary_max=salary_high,
                        currency=raw.get("currency_code") or None,
                        location=raw_location,
                        remote_type="remote" if is_remote else "onsite",
                        visa_sponsorship=bool(
                            visa
                            and _detect_visa(
                                relocation_paid=relocation_paid,
                                title=title,
                                description=raw.get("role_description"),
                                perks=raw.get("perks"),
                                tags=tags,
                            )
                        ),
                        portal_source="landingjobs",
                        portal_id=str(raw.get("id")) if raw.get("id") is not None else None,
                        raw_data={
                            "tags": tags,
                            "type": raw.get("type"),
                            "relocation_paid": relocation_paid,
                        },
                    )
                )
                if len(results) >= limit:
                    break

            if len(results) >= limit:
                break

        logger.info("Landing.jobs search returned %d results for query=%r", len(results), query)
        return results

    async def healthcheck(self) -> bool:
        """Return ``True`` if page 1 is reachable and contains jobs."""
        try:
            jobs = await self._fetch_page(1)
            return len(jobs) > 0
        except Exception:
            logger.exception("Landing.jobs healthcheck failed")
            return False


registry.register(LandingJobsPlugin())
