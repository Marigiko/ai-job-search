# .agents/skills/job-scraper/browser_runner.py
"""
Headless browser runner for non-blocking job applications.
All automation runs in background without showing a window.
"""
from pathlib import Path
import playwright.sync_api as _pw_sync

PROFILES_BASE = Path("/tmp/browser-profiles")


def _get_profile_dir(platform: str) -> Path:
    path = PROFILES_BASE / platform
    path.mkdir(parents=True, exist_ok=True)
    return path


def apply(job_url: str, platform: str, action: str = "submit") -> dict:
    """Apply to a job URL headlessly. Returns {"status": "ok"|"error", "detail": str}."""
    profile_dir = _get_profile_dir(platform)
    with _pw_sync.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(storage_state=_load_state(platform))
        page = context.new_page()
        page.goto(job_url)
        page.wait_for_load_state("networkidle", timeout=15000)
        result = _dispatch(page, platform, action)
        _save_state(platform, context.storage_state())
        browser.close()
        return result


def _dispatch(page, platform: str, action: str) -> dict:
    """Route to the right handler per platform."""
    handlers = {
        "getonbrd": _apply_getonbrd,
    }
    handler = handlers.get(platform)
    if not handler:
        return {"status": "error", "detail": f"Unknown platform: {platform}"}
    return handler(page)


def _apply_getonbrd(page) -> dict:
    """GetOnBoard: fill form, clear old content, submit."""
    return {"status": "ok", "detail": "GetOnBoard apply not yet implemented — see Task 2"}


def _load_state(platform: str) -> str | None:
    state_file = _get_profile_dir(platform) / "state.json"
    if state_file.exists():
        return str(state_file)
    return None


def _save_state(platform: str, state: dict) -> None:
    import json
    state_file = _get_profile_dir(platform) / "state.json"
    state_file.write_text(json.dumps(state))
