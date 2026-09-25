"""Portal plugin system — extensible job source integrations.

Import this module to register the bundled plugins with the global
:class:`PluginRegistry` singleton::

    from app.plugins import registry  # noqa: F401  (registers plugins)

After import, ``registry.list_names()`` returns the available portal keys.
"""

from __future__ import annotations

from app.plugins.arbeitnow import ArbeitnowPlugin
from app.plugins.base import PortalPlugin
from app.plugins.landingjobs import LandingJobsPlugin
from app.plugins.registry import PluginRegistry, registry
from app.plugins.remoteok import RemoteOkPlugin

__all__: list[str] = [
    "PortalPlugin",
    "PluginRegistry",
    "registry",
    "RemoteOkPlugin",
    "LandingJobsPlugin",
    "ArbeitnowPlugin",
]
