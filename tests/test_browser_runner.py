# tests/test_browser_runner.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import MagicMock, patch
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "browser_runner",
    Path(__file__).resolve().parent.parent / ".agents" / "skills" / "job-scraper" / "browser_runner.py",
)
browser_runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(browser_runner)

apply = browser_runner.apply
_get_profile_dir = browser_runner._get_profile_dir


def test_get_profile_dir_creates_and_returns_path():
    path = _get_profile_dir("getonbrd")
    assert "getonbrd" in str(path)
    assert path.exists()


def test_apply_launches_headless():
    mock_chromium = MagicMock()
    mock_browser = MagicMock()
    mock_chromium.launch.return_value = mock_browser
    mock_context = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_context.storage_state.return_value = {}
    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page

    mock_pw = MagicMock()
    mock_pw.chromium = mock_chromium

    with patch.object(browser_runner._pw_sync, "sync_playwright") as mock_sync:
        mock_sync.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_sync.return_value.__exit__ = MagicMock(return_value=False)

        apply("https://www.getonbrd.com/jobs/test", "getonbrd")

    mock_chromium.launch.assert_called_once()
    call_kwargs = mock_chromium.launch.call_args[1]
    assert call_kwargs["headless"] is True
