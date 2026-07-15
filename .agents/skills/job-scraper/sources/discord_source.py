# .agents/skills/job-scraper/sources/discord_source.py
"""Parse job postings shared via Discord."""
import re

def parse(text: str) -> dict:
    return {
        "title": _extract(text, [r"(?i)rol[:\s]*(.+)", r"(?i)position[:\s]*(.+)", r"(?i)role[:\s]*(.+)"]),
        "company": _extract(text, [r"(?i)empresa[:\s]*(.+)", r"(?i)company[:\s]*(.+)"]),
        "location": _extract(text, [r"(?i)ubicación[:\s]*(.+)", r"(?i)location[:\s]*(.+)"]),
        "salary": _extract(text, [r"(?i)salario[:\s]*(.+)", r"(?i)salary[:\s]*(.+)"]),
        "apply_email": _extract_email(text),
        "description": text.strip(),
        "url": None,
    }

def _extract(text: str, patterns: list[str]) -> str | None:
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return None

def _extract_email(text: str) -> str | None:
    deobfuscated = text.replace("[at]", "@").replace("[dot]", ".").replace("&#64;", "@")
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", deobfuscated)
    return m.group(0) if m else None
