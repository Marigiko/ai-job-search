"""Settings service — read/write key-value settings."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting

# Default values for all settings
DEFAULTS: dict[str, object] = {
    "smtp": {
        "host": "",
        "port": 587,
        "username": "",
        "password": "",
        "use_tls": True,
        "from_name": "",
        "from_email": "",
        "reply_to": None,
    },
    "api_keys": {
        "hunter": "",
        "apollo": "",
        "serper": "",
    },
    "outreach_limits": {
        "daily_max": 50,
        "hourly_max": 10,
        "delay_seconds": 30,
        "max_per_company": 2,
        "cooldown_hours": 72,
    },
}

# Static portal registry — enabled state is stored per-portal in DB
PORTAL_REGISTRY: list[dict[str, str]] = [
    {"id": "remoteok", "name": "RemoteOK", "description": "Remote jobs board", "category": "remote"},
    {"id": "landingjobs", "name": "Landing.jobs", "description": "European tech jobs", "category": "local"},
    {"id": "arbeitnow", "name": "Arbeitnow", "description": "Germany/EU remote-friendly", "category": "remote"},
    {"id": "indeed", "name": "Indeed", "description": "Global job aggregator", "category": "aggregator"},
    {"id": "linkedin", "name": "LinkedIn", "description": "Professional network jobs", "category": "aggregator"},
    {"id": "getonbrd", "name": "Get on Board", "description": "LatAm + remote tech", "category": "remote"},
    {"id": "jobicy", "name": "Jobicy", "description": "Remote jobs API", "category": "remote"},
]


async def get_json_setting(db: AsyncSession, key: str) -> object:
    """Return the parsed JSON value for a key, or the default."""
    result = await db.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        return DEFAULTS.get(key)
    try:
        return json.loads(row.value)
    except (json.JSONDecodeError, TypeError):
        return DEFAULTS.get(key)


async def set_json_setting(db: AsyncSession, key: str, value: object) -> None:
    """Persist a JSON-serializable value for a key."""
    result = await db.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()
    serialized = json.dumps(value)
    if row is None:
        row = Setting(key=key, value=serialized)
        db.add(row)
    else:
        row.value = serialized
    await db.flush()


async def get_all_settings(db: AsyncSession) -> dict[str, object]:
    """Return a dict with every settings key."""
    return {
        "smtp": await get_json_setting(db, "smtp"),
        "api_keys": await get_json_setting(db, "api_keys"),
        "outreach_limits": await get_json_setting(db, "outreach_limits"),
    }


async def get_portal_enabled_map(db: AsyncSession) -> dict[str, bool]:
    """Return a map of portal_id -> enabled (default True)."""
    raw = await get_json_setting(db, "portal_enabled")
    if isinstance(raw, dict):
        return raw
    return {}


async def set_portal_enabled(db: AsyncSession, portal_id: str, enabled: bool) -> None:
    """Toggle a single portal on/off."""
    enabled_map = await get_portal_enabled_map(db)
    enabled_map[portal_id] = enabled
    await set_json_setting(db, "portal_enabled", enabled_map)
