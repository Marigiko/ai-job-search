#!/usr/bin/env python3
"""Email extraction validator with fusion detection.

Usage:
  python scripts/validate_emails.py
  python scripts/validate_emails.py --export-clean
"""
import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict

OCR_FILE = Path(__file__).parent.parent / "jobs_images" / "ocr_results_2026-07-29.json"
SENT_FILE = Path(__file__).parent.parent / "data" / "batch_sent.json"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "email_validation_report.json"

# Valid TLDs (simple and compound)
VALID_TLDS = [
    # Compound (check first)
    "com.ar", "com.mx", "com.co", "com.br", "com.pe", "com.uy", "com.cl",
    "com.bo", "com.ec", "com.pa", "com.py", "co.uk", "org.uk",
    # Simple
    "com", "net", "org", "io", "co", "info", "biz", "me", "us", "uk",
    "es", "ar", "mx", "cl", "pe", "br", "uy", "py", "bo", "ec", "ai",
    "tech", "app", "dev", "agency", "online", "store", "site", "cloud",
]

# Words/sentences that commonly follow emails in OCR (fusion indicators)
FUSION_PATTERNS = [
    r'con\s', r'tu\s', r'el\s', r'la\s', r'de\s', r'en\s', r'por\s', r'para\s',
    r'una\s', r'del\s', r'hasta\s', r'envia\s', r'escribe\s', r'asunto\s',
    r'ref\s*[:.]', r'whatsapp\s*[+:]', r'tienes?\s', r'tiene\s', r'hoy\s',
    r'ahora\s', r'urgente', r'postulate\s', r'aplica\s', r'envianos\s',
    r'contactanos\s', r'trabajo\s', r'empleo\s', r'vacante\s', r'activa\s',
    r'buscamos\s', r'ecuador', r'colombia', r'mexico', r'argentina\s',
    r'chile\s', r'peru\s', r'uruguay\s', r'incluye\s', r'cuando\s',
    r'seguir\s', r'editado\s', r'oportunidad\s', r'seleccion\s',
    r'desarrollador\s', r'fullstack\s', r'backend\s', r'frontend\s',
    r'senior\s', r'junior\s', r'tiene\s', r'tiempo\s', r'fecha\s',
]


def extract_emails(text: str) -> list[str]:
    """Extract and clean emails from OCR text."""
    if not text:
        return []
    
    # Normalize
    normalized = text.replace('\n', ' ').replace('\r', ' ')
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Deobfuscation
    normalized = re.sub(r"\s*[\[\(]\s*at\s*[\]\)]\s*", "@", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s*[\[\(]\s*dot\s*[\]\)]\s*", ".", normalized, flags=re.IGNORECASE)
    normalized = normalized.replace("&#64;", "@")
    
    # Find all @ positions
    emails = []
    for match in re.finditer(r'@', normalized):
        pos = match.start()
        
        # Expand left
        left = pos - 1
        while left >= 0 and (normalized[left].isalnum() or normalized[left] in '._%+-'):
            left -= 1
        left += 1
        
        # Expand right (get more than needed, then trim)
        right = pos + 1
        while right < len(normalized) and (normalized[right].isalnum() or normalized[right] in '.-'):
            right += 1
        
        raw = normalized[left:right].strip()
        email = clean_email(raw)
        if email and '@' in email:
            emails.append(email)
    
    return emails


def clean_email(raw: str) -> str:
    """Clean a raw email string by removing fusion artifacts."""
    if not raw or '@' not in raw:
        return raw
    
    # Step 1: Remove trailing dots/commas
    cleaned = raw.rstrip('.,;:!?\'\"')
    
    # Step 2: Find valid TLD and truncate after it
    domain = cleaned.rsplit('@', 1)[1]
    
    # Try to find the longest valid TLD that ends the domain
    best_tld_len = 0
    for tld in VALID_TLDS:
        if domain.lower().endswith(tld):
            best_tld_len = max(best_tld_len, len(tld))
    
    if best_tld_len > 0:
        # Check if domain has extra text after the valid TLD
        domain_body = domain[:len(domain) - best_tld_len]
        extra = domain[len(domain) - best_tld_len + 1:]  # +1 to skip the dot before TLD
        
        if domain_body and extra:
            # Check if domain_body ends with . (valid domain part)
            # and extra starts with a fusion word
            pass  # Keep as is, we already extracted correctly
    
    # Step 3: Detect fusion by checking for sentence-like text after email
    # Look for patterns like "emailWord" where Word is a Spanish/English word
    for pattern in FUSION_PATTERNS:
        # Check if email is followed by fusion pattern
        match = re.search(r'(@[a-z0-9.\-]+\.[a-z]{2,4})' + pattern, cleaned, re.IGNORECASE)
        if match:
            # Truncate at the end of the TLD
            cleaned = match.group(1)
            break
    
    # Step 4: Truncate at the end of the first valid TLD
    # Find @domain.tld and cut off any trailing text (fusion)
    best_match = None
    best_tld_len = 0
    
    for tld in sorted(VALID_TLDS, key=len, reverse=True):
        # Find this TLD in the email
        idx = cleaned.lower().find('.' + tld)
        if idx >= 0:
            # Check if it's at end of string OR followed by non-domain char
            after_tld = idx + len(tld) + 1  # +1 for the dot
            if after_tld >= len(cleaned) or not cleaned[after_tld].isalnum() or cleaned[after_tld] == '.':
                # Check if TLD is preceded by a valid domain
                before = cleaned[:idx]
                if re.search(r'@[a-z0-9-]+(\.[a-z0-9-]+)*$', before, re.IGNORECASE):
                    if len(tld) > best_tld_len:
                        best_tld_len = len(tld)
                        best_match = cleaned[:after_tld]
            else:
                # TLD is followed by more text (fusion) - this is our boundary
                before = cleaned[:idx]
                if re.search(r'@[a-z0-9-]+(\.[a-z0-9-]+)*$', before, re.IGNORECASE):
                    candidate = cleaned[:after_tld]
                    if len(tld) > best_tld_len:
                        best_tld_len = len(tld)
                        best_match = candidate
    
    if best_match:
        cleaned = best_match
    
    # Step 5: Remove trailing non-email characters
    cleaned = re.sub(r'[^a-zA-Z0-9._%+\-@]+$', '', cleaned)
    
    return cleaned


def validate_email(email: str, image: str = '') -> dict:
    """Validate email quality."""
    issues = []
    confidence = 1.0
    
    if '@' not in email:
        return {"email": email, "confidence": 0, "issues": ["no @"], "needs_review": True, "image": image}
    
    local, domain = email.rsplit('@', 1)
    
    # Validate local part
    if len(local) < 2:
        issues.append("local muy corto")
        confidence -= 0.3
    if len(local) > 40:
        issues.append(f"local largo ({len(local)})")
        confidence -= 0.1
    
    # Validate domain
    if '.' not in domain:
        issues.append("dominio sin punto")
        confidence -= 0.3
    
    # Check TLD
    parts = domain.split('.')
    tld = parts[-1].lower()
    compound = f"{parts[-2]}.{parts[-1]}".lower() if len(parts) >= 2 else ''
    
    if compound in VALID_TLDS or tld in VALID_TLDS:
        pass  # Valid
    else:
        issues.append(f"TLD desconocido: .{tld}")
        confidence -= 0.2
    
    return {
        "email": email,
        "confidence": max(0, confidence),
        "issues": issues,
        "needs_review": confidence < 0.7,
        "image": image,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-clean", action="store_true")
    args = ap.parse_args()
    
    with open(OCR_FILE) as f:
        ocr_data = json.load(f)
    with open(SENT_FILE) as f:
        sent = json.load(f)
    
    print("="*70)
    print("VALIDACIÓN DE EMAILS v4 - Fusion-aware extraction")
    print("="*70)
    
    all_emails = []
    for r in ocr_data['results']:
        raw = r.get('raw_text', '') or ''
        image = (r.get('image_path') or '').split('/')[-1]
        
        emails = extract_emails(raw)
        for email in emails:
            all_emails.append((email, image))
    
    # Deduplicate
    seen = {}
    for email, image in all_emails:
        if email not in seen:
            seen[email] = image
    
    validations = []
    for email, image in seen.items():
        v = validate_email(email, image)
        validations.append(v)
    
    validations.sort(key=lambda x: x['confidence'])
    
    print(f"\nÚnicos: {len(validations)} | OK: {sum(1 for v in validations if not v['needs_review'])} | Revisar: {sum(1 for v in validations if v['needs_review'])}")
    
    print("\n" + "-"*70)
    print("EMAILS CON PROBLEMAS:")
    print("-"*70)
    
    for v in validations:
        if v['needs_review'] or v['issues']:
            status = "⚠️" if v['needs_review'] else "ℹ️"
            issues_str = f" [{'; '.join(v['issues'])}]" if v['issues'] else ""
            print(f"  {status} {v['email']:45s} ({v['confidence']:.0%}){issues_str}")
    
    not_sent = [v for v in validations if v['email'] not in sent]
    if not_sent:
        print(f"\n  NO ENVIADOS ({len(not_sent)}):")
        for v in not_sent:
            status = "⚠️" if v['needs_review'] else "✅"
            print(f"    [{status}] {v['email']}")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({"emails": validations}, f, ensure_ascii=False, indent=2)
    
    print(f"\n  Reporte: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
