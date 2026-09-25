#!/usr/bin/env python3
"""Email verification + Brasil application strategy.

Verifies emails exist before sending, and for Brasil specifically,
uses freehire direct URLs and career page scraping.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / ".env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()

HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY")


def verify_email_hunter(email: str) -> dict:
    """Verify an email via Hunter.io Email Verifier."""
    if not HUNTER_API_KEY:
        return {"status": "unknown", "email": email, "reason": "no_api_key"}
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_API_KEY}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ai-job-search/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        result = data.get("data", {})
        return {
            "email": email,
            "status": result.get("status", "unknown"),
            "score": result.get("score", 0),
            "regexp": result.get("regexp"),
            "gibberish": result.get("gibberish"),
            "result": result.get("result", "unknown"),
        }
    except Exception as e:
        return {"status": "error", "email": email, "reason": str(e)}


def verify_email_smtp(email: str) -> dict:
    """Basic SMTP verification (limited, many servers block)."""
    import socket
    import dns.resolver
    domain = email.split("@")[1]
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = str(mx_records[0].exchange).rstrip(".")
        # Just check if MX resolves - full SMTP verify is unreliable
        return {"email": email, "mx_found": True, "mx_host": mx_host, "status": "mx_ok"}
    except Exception as e:
        return {"email": email, "mx_found": False, "reason": str(e), "status": "mx_fail"}


def is_pattern_guessed(email: str) -> bool:
    """Check if email is pattern-guessed (low confidence)."""
    guessed_prefixes = [
        "careers@", "hr@", "jobs@", "contact@", "info@", "hello@",
        "founder@", "talent@", "recruiting@", "vagas@", "contato@",
        "karera@", "recrutamento@", "rh@", "trabalhe@"
    ]
    return any(email.lower().startswith(p) for p in guessed_prefixes)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Email verification + Brasil strategy")
    ap.add_argument("--verify", help="Verify a specific email")
    ap.add_argument("--verify-all", action="store_true", help="Verify all contacted emails")
    ap.add_argument("--list-guessed", action="store_true", help="List pattern-guessed emails")
    ap.add_argument("--br-strategy", action="store_true", help="Brasil application strategy")
    args = ap.parse_args()

    if args.verify:
        result = verify_email_hunter(args.verify)
        print(json.dumps(result, indent=2))
        return

    if args.list_guessed:
        dedup_file = Path(__file__).parent.parent / "data" / "contacted_emails.json"
        with open(dedup_file) as f:
            emails = json.load(f)
        guessed = [e for e in emails if is_pattern_guessed(e)]
        print(f"Pattern-guessed emails ({len(guessed)} total):")
        for e in guessed:
            print(f"  {e}")
        return

    if args.verify_all:
        dedup_file = Path(__file__).parent.parent / "data" / "contacted_emails.json"
        with open(dedup_file) as f:
            emails = json.load(f)
        print(f"Verifying {len(emails)} emails...")
        results = []
        for email in emails:
            result = verify_email_hunter(email)
            results.append(result)
            status_icon = {
                "valid": "✅",
                "invalid": "❌",
                "accept_all": "⚠️",
                "webmail": "📧",
                "disposable": "🗑️",
                "unknown": "❓",
            }.get(result.get("status", "unknown"), "?")
            print(f"  {status_icon} {email}: {result.get('status', '?')} (score: {result.get('score', '?')})")

        valid = [r for r in results if r.get("status") == "valid"]
        invalid = [r for r in results if r.get("status") == "invalid"]
        print(f"\nValid: {len(valid)}")
        print(f"Invalid: {len(invalid)}")
        return

    if args.br_strategy:
        print("=== Brasil Application Strategy ===")
        print()
        print("Problem: Pattern-guessed emails (careers@, hr@, etc.) bounce at ~90% rate")
        print()
        print("Solution:")
        print("1. Use freehire.dev direct URLs (apply on company career pages)")
        print("2. Scrape 'trabalhe conosco' / 'vagas' pages for real emails")
        print("3. Use LinkedIn to find recruiters at target companies")
        print("4. Use Hunter.io verify before sending any email")
        print("5. Focus on companies with verified emails only")
        print()
        print("For Brasil specifically, common real email patterns:")
        print("  - rh@domain.com.br (most common)")
        print("  - vagas@domain.com.br")
        print("  - trabalheconosco@domain.com.br")
        print("  - talentos@domain.com.br")
        print("  - Many use LinkedIn or Gupy (ATS) for applications")
        print()
        print("Best approach: Apply via freehire URLs directly, not email.")
        return


if __name__ == "__main__":
    main()
