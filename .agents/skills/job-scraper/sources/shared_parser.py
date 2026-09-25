# .agents/skills/job-scraper/sources/shared_parser.py
"""Shared job-text parsing helpers used by all source parsers and OCR."""
import re

# Valid TLDs for email boundary detection (longer/compound first)
_VALID_TLDS = [
    # Compound TLDs
    "com.ar", "com.mx", "com.co", "com.br", "com.pe", "com.uy", "com.cl",
    "com.bo", "com.ec", "com.pa", "com.py", "co.uk", "org.uk",
    # Simple TLDs
    "com", "net", "org", "io", "co", "info", "biz", "me", "us", "uk",
    "es", "ar", "mx", "cl", "pe", "br", "uy", "py", "bo", "ec", "ai",
    "tech", "app", "dev", "agency", "online", "store", "site", "cloud",
]

# Spanish words commonly fused after a TLD by OCR
_FUSED_WORDS = frozenset(
    {'con', 'para', 'en', 'y', 'o', 'de', 'del', 'al', 'el', 'la',
     'las', 'los', 'por', 'hola', 'gracias', 'saludos', 'cv', 'tel'}
)


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
    """Extract email with TLD-aware boundary detection and fusion removal."""
    if not text:
        return None

    # Deobfuscation
    deobf = re.sub(r"\s*[\[\(]\s*at\s*[\]\)]\s*", "@", text, flags=re.IGNORECASE)
    deobf = re.sub(r"\s*[\[\(]\s*dot\s*[\]\)]\s*", ".", deobf, flags=re.IGNORECASE)
    deobf = deobf.replace("&#64;", "@")

    # Find all @ positions
    candidates = []
    for match in re.finditer(r'@', deobf):
        pos = match.start()

        # Expand left (local part)
        left = pos - 1
        while left >= 0 and (deobf[left].isalnum() or deobf[left] in '._%+-'):
            left -= 1
        left += 1

        # Expand right (domain part - get more than needed)
        right = pos + 1
        while right < len(deobf) and (deobf[right].isalnum() or deobf[right] in '.-'):
            right += 1

        raw = deobf[left:right].strip(' .,;:!?\'\"')
        cleaned = _truncate_at_valid_tld(raw)
        if cleaned and '@' in cleaned and '.' in cleaned.split('@')[1]:
            candidates.append(cleaned)

    # Return first valid candidate
    for c in candidates:
        if re.match(r'^[a-zA-Z0-9._%+\-]{2,64}@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', c):
            return c

    return None


def _truncate_at_valid_tld(email: str) -> str:
    """Truncate email at the end of the first valid TLD to remove fusion artifacts."""
    if '@' not in email:
        return email

    best_match = None
    best_tld_len = 0

    fused = _FUSED_WORDS

    at_idx = email.find('@')
    domain = email[at_idx + 1:].lower()

    for tld in _VALID_TLDS:
        idx = domain.find('.' + tld)
        if idx >= 0:
            after_tld = idx + len(tld) + 1
            # Check if TLD is at end OR followed by non-domain char (fusion)
            if after_tld <= len(domain):
                before = domain[:idx]
                if re.search(r'[a-zA-Z0-9._%+\-]+$', before) and (
                    after_tld == len(domain)
                    or not (domain[after_tld].isalnum() or domain[after_tld] in '.-')
                    or (m := re.match(r'[a-z]+', domain[after_tld:]))
                    and m.group(0) in fused
                ):
                    if len(tld) > best_tld_len:
                        best_tld_len = len(tld)
                        best_match = email[:at_idx + 1 + after_tld]

    return best_match if best_match else email


def extract_url(text: str) -> str | None:
    m = re.search(r"https?://[^\s\"'<>]+", text)
    return m.group(0).rstrip(").,;") if m else None
