"""Load the candidate profile from profile.local.json (fallback: profile.example.json).

Personal contact data lives in profile.local.json (gitignored); tracked files
only ever see the placeholders from profile.example.json.
"""
import json
import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def load_profile() -> dict:
    """Return the candidate profile dict, preferring profile.local.json."""
    for name in ("profile.local.json", "profile.example.json"):
        path = _REPO_ROOT / name
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}


PROFILE = load_profile()


def get_sender() -> str:
    """Resolve the sending email: GMAIL_SENDER env var, then profile, then placeholder."""
    return os.getenv("GMAIL_SENDER") or PROFILE.get("email", "you@example.com")
