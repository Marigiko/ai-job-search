"""Load environment variables from .env file (no external dependencies)."""
import os
from pathlib import Path

def load_env(dotenv_path: str | None = None) -> None:
    """Load key=value pairs from .env into os.environ (if not already set)."""
    if dotenv_path is None:
        # Walk up from this file to find .env
        current = Path(__file__).resolve().parent.parent
        dotenv_path = current / ".env"
    else:
        dotenv_path = Path(dotenv_path)
    if not dotenv_path.exists():
        return
    with open(dotenv_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value
