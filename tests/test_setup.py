# tests/test_setup.py
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent

def test_setup_sh_exists():
    setup = ROOT / "setup.sh"
    assert setup.exists()
    content = setup.read_text()
    assert "pip install" in content
    assert "bun install" in content
    assert "playwright install" in content

def test_requirements_txt_has_all_deps():
    reqs = (ROOT / "requirements.txt").read_text().lower()
    assert "pytesseract" in reqs
    assert "pillow" in reqs
    assert "python-dotenv" in reqs
    assert "pyyaml" in reqs

def test_env_gitignored():
    gitignore = (ROOT / ".gitignore").read_text()
    assert ".env" in gitignore
