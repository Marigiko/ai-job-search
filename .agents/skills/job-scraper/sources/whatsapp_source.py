# .agents/skills/job-scraper/sources/whatsapp_source.py
"""Parse job postings shared via WhatsApp."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared_parser import parse_job_text


def parse(text: str) -> dict:
    return parse_job_text(text)
