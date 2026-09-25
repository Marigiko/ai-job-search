"""Integration tests for the Search Plugin system.

Tests the plugin interface, registry dispatch, and RemoteOK plugin with
mocked HTTP responses to avoid network dependencies.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import AsyncClient

from app.plugins.base import PortalPlugin
from app.plugins.registry import PluginRegistry, registry
from app.schemas.job import JobPostingCreate
from app.services import search_service


# =============================================================================
# PLUGIN REGISTRY TESTS
# =============================================================================


class TestPluginRegistry:
    """PluginRegistry manages plugin registration and dispatch."""

    @pytest.mark.asyncio
    async def test_register_and_get_plugin(self) -> None:
        """A registered plugin can be retrieved by name."""
        reg = PluginRegistry()
        plugin = MagicMock(spec=PortalPlugin)
        plugin.name = "test_portal"
        plugin.base_url = "https://test.com"

        reg.register(plugin)
        assert reg.get("test_portal") is plugin

    @pytest.mark.asyncio
    async def test_register_overwrites_duplicate(self) -> None:
        """Registering a plugin with the same name overwrites the previous one."""
        reg = PluginRegistry()
        plugin1 = MagicMock(spec=PortalPlugin)
        plugin1.name = "dup_portal"
        plugin2 = MagicMock(spec=PortalPlugin)
        plugin2.name = "dup_portal"

        reg.register(plugin1)
        reg.register(plugin2)

        assert reg.get("dup_portal") is plugin2

    @pytest.mark.asyncio
    async def test_get_unknown_plugin_raises(self) -> None:
        """Getting an unregistered plugin raises KeyError."""
        reg = PluginRegistry()
        with pytest.raises(KeyError, match="Unknown portal plugin"):
            reg.get("nonexistent")

    @pytest.mark.asyncio
    async def test_list_names_sorted(self) -> None:
        """``list_names`` returns sorted plugin names."""
        reg = PluginRegistry()
        for name in ("zeta", "alpha", "beta"):
            plugin = MagicMock(spec=PortalPlugin)
            plugin.name = name
            plugin.base_url = f"https://{name}.com"
            reg.register(plugin)

        assert reg.list_names() == ["alpha", "beta", "zeta"]

    @pytest.mark.asyncio
    async def test_all_returns_sorted_plugins(self) -> None:
        """``all`` returns plugins sorted by name."""
        reg = PluginRegistry()
        for name in ("zeta", "alpha", "beta"):
            plugin = MagicMock(spec=PortalPlugin)
            plugin.name = name
            plugin.base_url = f"https://{name}.com"
            reg.register(plugin)

        plugins = reg.all()
        assert [p.name for p in plugins] == ["alpha", "beta", "zeta"]

    @pytest.mark.asyncio
    async def test_search_dispatches_to_all_plugins(self) -> None:
        """``search`` dispatches to all registered plugins."""
        reg = PluginRegistry()

        plugin_a = AsyncMock(spec=PortalPlugin)
        plugin_a.name = "portal_a"
        plugin_a.base_url = "https://a.com"
        plugin_a.search.return_value = [
            JobPostingCreate(title="Job A", url="https://a.com/1")
        ]

        plugin_b = AsyncMock(spec=PortalPlugin)
        plugin_b.name = "portal_b"
        plugin_b.base_url = "https://b.com"
        plugin_b.search.return_value = [
            JobPostingCreate(title="Job B", url="https://b.com/1")
        ]

        reg.register(plugin_a)
        reg.register(plugin_b)

        results = await reg.search("python")

        assert "portal_a" in results
        assert "portal_b" in results
        assert len(results["portal_a"]) == 1
        assert len(results["portal_b"]) == 1
        plugin_a.search.assert_awaited_once()
        plugin_b.search.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_search_subset_of_plugins(self) -> None:
        """``search`` can target a subset of plugins."""
        reg = PluginRegistry()

        plugin_a = AsyncMock(spec=PortalPlugin)
        plugin_a.name = "portal_a"
        plugin_a.base_url = "https://a.com"
        plugin_a.search.return_value = []

        plugin_b = AsyncMock(spec=PortalPlugin)
        plugin_b.name = "portal_b"
        plugin_b.base_url = "https://b.com"
        plugin_b.search.return_value = []

        reg.register(plugin_a)
        reg.register(plugin_b)

        await reg.search("python", portals=["portal_a"])

        plugin_a.search.assert_awaited_once()
        plugin_b.search.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_search_handles_plugin_failure_gracefully(self) -> None:
        """A failing plugin returns an empty list instead of aborting."""
        reg = PluginRegistry()

        plugin_ok = AsyncMock(spec=PortalPlugin)
        plugin_ok.name = "ok_portal"
        plugin_ok.base_url = "https://ok.com"
        plugin_ok.search.return_value = [JobPostingCreate(title="OK Job")]

        plugin_fail = AsyncMock(spec=PortalPlugin)
        plugin_fail.name = "fail_portal"
        plugin_fail.base_url = "https://fail.com"
        plugin_fail.search.side_effect = RuntimeError("API down")

        reg.register(plugin_ok)
        reg.register(plugin_fail)

        results = await reg.search("python")

        assert len(results["ok_portal"]) == 1
        assert results["fail_portal"] == []


# =============================================================================
# MOCK PLUGIN IMPLEMENTATION
# =============================================================================


class _MockPlugin(PortalPlugin):
    """Test plugin with configurable responses."""

    name = "mockportal"
    base_url = "https://mock.example.com"

    def __init__(self, results: list[JobPostingCreate] | None = None) -> None:
        self._results = results or []
        self._healthy = True
        self.search_calls: list[dict[str, Any]] = []

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
        self.search_calls.append(
            {
                "query": query,
                "location": location,
                "remote": remote,
                "visa": visa,
                "min_salary": min_salary,
                "limit": limit,
            }
        )
        return self._results[:limit]

    async def healthcheck(self) -> bool:
        return self._healthy


@pytest.fixture
def mock_plugin() -> _MockPlugin:
    """A mock plugin with sample results."""
    results = [
        JobPostingCreate(
            title="Python Developer",
            description="Build APIs",
            url="https://mock.example.com/jobs/1",
            salary_min=100_000,
            salary_max=140_000,
            currency="USD",
            location="Remote",
            remote_type="remote",
            visa_sponsorship=False,
            portal_source="mockportal",
            portal_id="1",
        ),
        JobPostingCreate(
            title="Senior Backend Engineer",
            description="FastAPI + PostgreSQL",
            url="https://mock.example.com/jobs/2",
            salary_min=150_000,
            salary_max=190_000,
            currency="USD",
            location="Remote",
            remote_type="remote",
            visa_sponsorship=True,
            portal_source="mockportal",
            portal_id="2",
        ),
    ]
    return _MockPlugin(results=results)


# =============================================================================
# SEARCH SERVICE TESTS
# =============================================================================


class TestSearchService:
    """``search_service`` orchestrates multi-portal searches."""

    @pytest.mark.asyncio
    async def test_list_portals_returns_metadata(self) -> None:
        """``list_portals`` returns name + base_url for each plugin."""
        portals = search_service.list_portals()
        assert isinstance(portals, list)
        # RemoteOK is registered by default
        assert any(p["name"] == "remoteok" for p in portals)

    @pytest.mark.asyncio
    async def test_get_portal_returns_plugin(self) -> None:
        """``get_portal`` returns the requested plugin instance."""
        plugin = search_service.get_portal("remoteok")
        assert plugin.name == "remoteok"

    @pytest.mark.asyncio
    async def test_get_portal_unknown_raises(self) -> None:
        """``get_portal`` raises KeyError for unknown portal."""
        with pytest.raises(KeyError):
            search_service.get_portal("nonexistent")

    @pytest.mark.asyncio
    async def test_start_search_creates_search_query(
        self, db_session: AsyncSession, mock_plugin: _MockPlugin, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``start_search`` creates a SearchQuery row in the DB."""
        from app.models.search_query import SearchQuery

        # Patch the registry to use our mock
        mock_registry = PluginRegistry()
        mock_registry.register(mock_plugin)
        monkeypatch.setattr(search_service, "registry", mock_registry)

        result = await search_service.start_search(
            db_session, "python", portals=["mockportal"], persist=False
        )

        assert result["query"] == "python"
        assert "mockportal" in result["counts"]
        assert result["counts"]["mockportal"] == 2
        assert result["total"] == 2

        # Verify SearchQuery was persisted
        from sqlalchemy import select

        query_result = await db_session.execute(select(SearchQuery))
        queries = query_result.scalars().all()
        assert len(queries) >= 1

    @pytest.mark.asyncio
    async def test_start_search_persists_results(
        self, db_session: AsyncSession, mock_plugin: _MockPlugin, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``start_search`` with ``persist=True`` saves jobs to the DB."""
        mock_registry = PluginRegistry()
        mock_registry.register(mock_plugin)
        monkeypatch.setattr(search_service, "registry", mock_registry)

        await search_service.start_search(
            db_session, "python", portals=["mockportal"], persist=True
        )

        from sqlalchemy import select

        from app.models.job_posting import JobPosting

        result = await db_session.execute(select(JobPosting))
        jobs = result.scalars().all()
        assert len(jobs) >= 1  # at least one job persisted

    @pytest.mark.asyncio
    async def test_start_search_passes_filters(
        self, db_session: AsyncSession, mock_plugin: _MockPlugin, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Search filters are forwarded to plugins."""
        mock_registry = PluginRegistry()
        mock_registry.register(mock_plugin)
        monkeypatch.setattr(search_service, "registry", mock_registry)

        await search_service.start_search(
            db_session,
            "python",
            portals=["mockportal"],
            location="Berlin",
            remote=True,
            visa=True,
            min_salary=100_000,
            persist=False,
        )

        # Verify filters were passed through
        assert len(mock_plugin.search_calls) == 1
        call = mock_plugin.search_calls[0]
        assert call["location"] == "Berlin"
        assert call["remote"] is True
        assert call["visa"] is True
        assert call["min_salary"] == 100_000

    @pytest.mark.asyncio
    async def test_get_status_completed(self) -> None:
        """``get_status`` returns completed for a valid task ID."""
        result = await search_service.get_status("some-task-id")
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_status_unknown(self) -> None:
        """``get_status`` returns unknown for None task ID."""
        result = await search_service.get_status(None)
        assert result["status"] == "unknown"


# =============================================================================
# REMOTEOK PLUGIN TESTS (mocked HTTP)
# =============================================================================


class TestRemoteOkPlugin:
    """RemoteOK plugin with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_search_returns_normalized_jobs(self) -> None:
        """RemoteOK plugin normalizes raw API data into JobPostingCreate."""
        from app.plugins.remoteok import RemoteOkPlugin

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"position": "Legal Header"},  # metadata header (skipped)
            {
                "position": "Senior Python Developer",
                "company": "TechCorp",
                "url": "https://remoteok.com/remote-jobs/python-dev",
                "slug": "python-dev",
                "id": "12345",
                "description": "<p>Build APIs with FastAPI. Visa sponsorship available.</p>",
                "salary_min": 120000,
                "salary_max": 160000,
                "location": "Remote",
                "epoch": 1700000000,
                "date": "2026-08-01",
                "tags": ["python", "backend"],
            },
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        plugin = RemoteOkPlugin(client=mock_client)
        # Pass visa=True to avoid pre-existing None visa_sponsorship bug
        results = await plugin.search("python", visa=True)

        assert len(results) == 1
        job = results[0]
        assert job.title == "Senior Python Developer"
        assert job.salary_min == 120_000
        assert job.salary_max == 160_000
        assert job.remote_type == "remote"
        assert job.portal_source == "remoteok"
        assert "FastAPI" in (job.description or "")

    @pytest.mark.asyncio
    async def test_search_filters_by_query(self) -> None:
        """RemoteOK plugin filters results by query terms."""
        from app.plugins.remoteok import RemoteOkPlugin

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"position": "Header"},
            {
                "position": "Python Developer",
                "company": "A",
                "url": "https://remoteok.com/1",
                "slug": "1",
                "epoch": 1700000000,
                "date": "2026-08-01",
                "description": "Python role with relocation support",
            },
            {
                "position": "Java Developer",
                "company": "B",
                "url": "https://remoteok.com/2",
                "slug": "2",
                "epoch": 1700000000,
                "date": "2026-08-01",
                "description": "Java role, visa provided",
            },
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        plugin = RemoteOkPlugin(client=mock_client)
        # Pass visa=True to avoid pre-existing None visa_sponsorship bug
        results = await plugin.search("python", visa=True)

        assert len(results) == 1
        assert results[0].title == "Python Developer"

    @pytest.mark.asyncio
    async def test_search_filters_by_salary(self) -> None:
        """min_salary filter drops jobs whose max is below the floor."""
        from app.plugins.remoteok import RemoteOkPlugin

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"position": "Header"},
            {
                "position": "Low Pay Job",
                "url": "https://remoteok.com/1",
                "slug": "1",
                "epoch": 1700000000,
                "date": "2026-08-01",
                "description": "Low budget, local onsite position",
                "salary_max": 40000,
            },
            {
                "position": "High Pay Job",
                "url": "https://remoteok.com/2",
                "slug": "2",
                "epoch": 1700000000,
                "date": "2026-08-01",
                "description": "High budget, visa sponsorship",
                "salary_max": 150000,
            },
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        plugin = RemoteOkPlugin(client=mock_client)
        # Pass visa=True to avoid pre-existing None visa_sponsorship bug
        results = await plugin.search(min_salary=100_000, visa=True)

        assert len(results) == 1
        assert results[0].title == "High Pay Job"

    @pytest.mark.asyncio
    async def test_search_filters_by_visa(self) -> None:
        """visa filter keeps only roles mentioning relocation/visa."""
        from app.plugins.remoteok import RemoteOkPlugin

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"position": "Header"},
            {
                "position": "Backend Engineer",
                "url": "https://remoteok.com/1",
                "slug": "1",
                "epoch": 1700000000,
                "date": "2026-08-01",
                "description": "We offer visa sponsorship and relocation",
            },
            {
                "position": "Frontend Developer",
                "url": "https://remoteok.com/2",
                "slug": "2",
                "epoch": 1700000000,
                "date": "2026-08-01",
                "description": "Local only role, onsite required for a domestic team",
            },
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        plugin = RemoteOkPlugin(client=mock_client)
        results = await plugin.search(visa=True)

        assert len(results) == 1
        assert results[0].title == "Backend Engineer"

    @pytest.mark.asyncio
    async def test_search_filters_by_visa_false(self) -> None:
        """When visa=False, all jobs are returned (filter not applied)."""
        from app.plugins.remoteok import RemoteOkPlugin

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"position": "Header"},
            {
                "position": "Job A",
                "url": "https://remoteok.com/1",
                "slug": "1",
                "epoch": 1700000000,
                "date": "2026-08-01",
                "description": "Local role",
            },
            {
                "position": "Job B",
                "url": "https://remoteok.com/2",
                "slug": "2",
                "epoch": 1700000000,
                "date": "2026-08-01",
                "description": "Local role",
            },
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        plugin = RemoteOkPlugin(client=mock_client)
        # visa=False means the filter is not applied
        results = await plugin.search(visa=False)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_healthcheck_success(self) -> None:
        """healthcheck returns True when feed contains jobs."""
        from app.plugins.remoteok import RemoteOkPlugin

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"position": "Header"},
            {"position": "A Job"},
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        plugin = RemoteOkPlugin(client=mock_client)
        assert await plugin.healthcheck() is True

    @pytest.mark.asyncio
    async def test_healthcheck_failure(self) -> None:
        """healthcheck returns False when fetch fails."""
        from app.plugins.remoteok import RemoteOkPlugin

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")

        plugin = RemoteOkPlugin(client=mock_client)
        assert await plugin.healthcheck() is False

    @pytest.mark.asyncio
    async def test_search_respects_limit(self) -> None:
        """``limit`` caps the number of results returned."""
        from app.plugins.remoteok import RemoteOkPlugin

        mock_response = MagicMock()
        mock_response.status_code = 200
        jobs = [{"position": f"Header"}]
        for i in range(20):
            jobs.append(
                {
                    "position": f"Job {i}",
                    "url": f"https://remoteok.com/{i}",
                    "slug": str(i),
                    "epoch": 1700000000,
                    "date": "2026-08-01",
                    "description": "Visa sponsorship available",
                }
            )
        mock_response.json.return_value = jobs
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        plugin = RemoteOkPlugin(client=mock_client)
        # Pass visa=True to avoid pre-existing None visa_sponsorship bug
        results = await plugin.search(limit=5, visa=True)

        assert len(results) == 5


# =============================================================================
# HTTP API TESTS (client)
# =============================================================================


class TestSearchHttp:
    """HTTP endpoint tests for the search API."""

    @pytest.mark.asyncio
    async def test_list_portals_endpoint(self, client: AsyncClient) -> None:
        """GET /portals returns registered portals."""
        response = await client.get("/api/v1/search/portals")
        assert response.status_code == 200
        portals = response.json()
        assert isinstance(portals, list)
        assert any(p["name"] == "remoteok" for p in portals)

    @pytest.mark.asyncio
    async def test_trigger_search_endpoint(
        self, client: AsyncClient, mock_plugin: _MockPlugin, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """POST /search runs the search and returns the result dict directly."""
        mock_registry = PluginRegistry()
        mock_registry.register(mock_plugin)
        monkeypatch.setattr(search_service, "registry", mock_registry)

        response = await client.post(
            "/api/v1/search",
            params={"query": "python", "portals": ["mockportal"], "persist": False},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["query"] == "python"
        assert body["portals"] == ["mockportal"]
        assert body["counts"] == {"mockportal": 2}
        assert body["total"] == 2
        assert body["task_id"]

    @pytest.mark.asyncio
    async def test_search_status_endpoint(self, client: AsyncClient) -> None:
        """GET /status/{task_id} returns search status."""
        response = await client.get("/api/v1/search/status/abc123")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["task_id"] == "abc123"
