# tests/test_portal_cleaner.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import MagicMock
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "portal_cleaner",
    Path(__file__).resolve().parent.parent / ".agents" / "skills" / "job-scraper" / "portal_cleaner.py",
)
portal_cleaner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(portal_cleaner)

clean = portal_cleaner.clean


def test_clean_clears_trix_editors():
    page = MagicMock()
    editor = MagicMock()
    page.query_selector_all.return_value = [editor]

    clean(page, "getonbrd")

    editor.evaluate.assert_called()
    editor.dispatch_event.assert_called()


def test_clean_selects_resume():
    page = MagicMock()
    option1 = MagicMock()
    option1.get_attribute.return_value = ""
    option2 = MagicMock()
    option2.get_attribute.return_value = "123"
    select = MagicMock()
    select.query_selector_all.return_value = [option1, option2]
    page.query_selector.return_value = select

    clean(page, "getonbrd")

    select.select_option.assert_called_with("123")


def test_clean_clears_salary_and_reason():
    page = MagicMock()
    page.query_selector_all.return_value = []
    salary = MagicMock()
    reason = MagicMock()
    page.query_selector.side_effect = [None, salary, reason]

    clean(page, "getonbrd")

    salary.fill.assert_called_with("")
    reason.fill.assert_called_with("")
