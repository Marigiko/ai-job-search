"""Plugin registry — discovers, registers and dispatches portal plugins."""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.plugins.base import PortalPlugin
from app.schemas.job import JobPostingCreate

logger = get_logger(__name__)


class PluginRegistry:
    """In-memory registry of portal plugins keyed by :attr:`PortalPlugin.name`.

    Plugins register themselves via :meth:`register`, typically from their
    module-level ``register`` call. The registry also exposes convenience
    helpers to dispatch searches across *all* or a *subset* of portals.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, PortalPlugin] = {}

    def register(self, plugin: PortalPlugin) -> None:
        """Add a plugin instance. Overwrites any existing entry with the same name."""
        if plugin.name in self._plugins:
            logger.warning("Overwriting existing plugin registration: %s", plugin.name)
        self._plugins[plugin.name] = plugin
        logger.info("Registered portal plugin: %s", plugin.name)

    def get(self, name: str) -> PortalPlugin:
        """Look up a plugin by name.

        Raises:
            KeyError: if no plugin with ``name`` is registered.
        """
        try:
            return self._plugins[name]
        except KeyError:
            available = sorted(self._plugins.keys())
            raise KeyError(
                f"Unknown portal plugin '{name}'. Available: {available}"
            ) from None

    def list_names(self) -> list[str]:
        """Return sorted registered plugin names."""
        return sorted(self._plugins.keys())

    def all(self) -> list[PortalPlugin]:
        """Return all registered plugins sorted by name."""
        return [self._plugins[name] for name in sorted(self._plugins)]

    async def search(
        self,
        query: str | None = None,
        portals: list[str] | None = None,
        *,
        location: str | None = None,
        remote: bool | None = None,
        visa: bool | None = None,
        min_salary: int | None = None,
        jobage: int | None = None,
        limit: int = 50,
        page: int = 1,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, list[JobPostingCreate]]:
        """Dispatch a search to the requested portals (default: all).

        Returns a dict of ``{plugin_name: [JobPostingCreate, ...]}``. Plugins
        that fail at runtime are logged and return an empty list rather than
        aborting the whole batch — callers get partial results instead of none.
        """
        targets = (
            [self.get(name) for name in portals] if portals else self.all()
        )
        results: dict[str, list[PortalPlugin]] = {}
        for plugin in targets:
            try:
                results[plugin.name] = await plugin.search(
                    query,
                    location=location,
                    remote=remote,
                    visa=visa,
                    min_salary=min_salary,
                    jobage=jobage,
                    limit=limit,
                    page=page,
                    extra=extra,
                )
            except Exception:
                logger.exception("Plugin search failed: %s", plugin.name)
                results[plugin.name] = []
        return results


# Module-level singleton — import this from app.plugins.registry
registry = PluginRegistry()
