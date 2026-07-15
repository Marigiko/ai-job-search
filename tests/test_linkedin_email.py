# tests/test_linkedin_email.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "linkedin_email_apply",
    Path(__file__).resolve().parent.parent / ".agents" / "skills" / "job-scraper" / "linkedin_email_apply.py",
)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

get_apply_email = mod.get_apply_email
_deobfuscate_email = mod._deobfuscate_email


def test_get_apply_email_plain():
    text = "Interested? Send your CV to jobs@techcorp.com"
    assert get_apply_email(text) == "jobs@techcorp.com"


def test_get_apply_email_obfuscated():
    text = "Send CV to hola [at] empresa [dot] com"
    assert get_apply_email(text) == "hola@empresa.com"


def test_get_apply_email_entity():
    text = "Send CV to hire@company.com"
    assert get_apply_email(text) == "hire@company.com"


def test_no_email_returns_none():
    text = "Apply via our careers page"
    assert get_apply_email(text) is None


def test_deobfuscate():
    assert _deobfuscate_email("test [at] domain [dot] com") == "test@domain.com"
    assert _deobfuscate_email("&#64;domain.com") == "@domain.com"
