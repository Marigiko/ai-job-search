# .agents/skills/job-scraper/sources/whatsapp_source.py
"""Parse job postings shared via WhatsApp."""
import re

def parse(text: str) -> dict:
    return {
        "title": _extract(text, [r"(?i)rol[:\s]*(.+)", r"(?i)posición[:\s]*(.+)", r"(?i)vacante[:\s]*(.+)"]),
        "company": _extract(text, [r"(?i)empresa[:\s]*(.+)", r"(?i)compañía[:\s]*(.+)", r"(?i)company[:\s]*(.+)"]),
        "location": _extract(text, [r"(?i)ubicación[:\s]*(.+)", r"(?i)location[:\s]*(.+)", r"(?i)modalidad[:\s]*(.+)"]),
        "salary": _extract(text, [r"(?i)salario[:\s]*(.+)", r"(?i)salary[:\s]*(.+)", r"(?i)pago[:\s]*(.+)"]),
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
    deobfuscated = re.sub(r"\s*\[at\]\s*", "@", text)
    deobfuscated = re.sub(r"\s*\[dot\]\s*", ".", deobfuscated)
    deobfuscated = deobfuscated.replace("&#64;", "@")
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", deobfuscated)
    return m.group(0) if m else None
