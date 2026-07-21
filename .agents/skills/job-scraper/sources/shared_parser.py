# .agents/skills/job-scraper/sources/shared_parser.py
"""Shared job-text parsing helpers used by all source parsers and OCR."""
import re


def parse_job_text(text: str) -> dict:
    """Extract structured job fields from raw posting text."""
    return {
        "title": extract_field(text, [
            r"(?i)(?:title|puesto|vacante|rol|position|role)[:\s]*([^\n]+)",
            r"(?i)(?:buscamos|seeking|looking for)[:\s]*([^\n]+)",
        ]),
        "company": extract_field(text, [
            r"(?i)(?:empresa|compañía|company|organización)[:\s]*([^\n]+)",
            r"(?i)(?:@|en)\s+([A-Z][\w&.\- ]{1,40})(?:\s|$)",
        ]),
        "location": extract_field(text, [
            r"(?i)(?:ubicación|location|locación|ciudad|modalidad|place)[:\s]*([^\n]+)",
        ]),
        "salary": extract_field(text, [
            r"(?i)(?:salario|salary|remuneración|pago|pay|compensación)[:\s]*([$\d.,\s\-/]+(?:USD|EUR|ARS|(?:\w+/\w+))?[^\n]*)",
        ]),
        "apply_email": extract_email(text),
        "description": text.strip()[:4000],
        "url": extract_url(text),
    }


def extract_field(text: str, patterns: list[str]) -> str | None:
    for p in patterns:
        m = re.search(p, text)
        if m:
            val = m.group(1).strip()
            if val:
                return val
    return None


def extract_email(text: str) -> str | None:
    deobfuscated = re.sub(r"\s*[\[\(]\s*at\s*[\]\)]\s*", "@", text, flags=re.IGNORECASE)
    deobfuscated = re.sub(r"\s*[\[\(]\s*dot\s*[\]\)]\s*", ".", deobfuscated, flags=re.IGNORECASE)
    deobfuscated = deobfuscated.replace("&#64;", "@")
    deobfuscated = re.sub(r"\s+at\s+(?=[a-z0-9.-]+\.[a-z]{2,})", "@", deobfuscated, flags=re.IGNORECASE)
    deobfuscated = re.sub(r"\s+dot\s+", ".", deobfuscated, flags=re.IGNORECASE)
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", deobfuscated)
    return m.group(0) if m else None


def extract_url(text: str) -> str | None:
    m = re.search(r"https?://[^\s\"'<>]+", text)
    return m.group(0).rstrip(").,;") if m else None
