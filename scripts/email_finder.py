#!/usr/bin/env python3
"""Email finder module — unified interface for finding founder/CTO emails.

Supports multiple backends:
  - hunter.io: Domain search + email finder (25 free searches/month)
  - apollo.io: Contact search with emails (60 free credits/month)
  - pattern guessing: founder@domain, first@domain (free, low accuracy)

Usage:
  python email_finder.py --domain acme.io --role founder
  python email_finder.py --domain acme.io --role founder --verify
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

from env_loader import load_env
load_env()


def find_email_hunter(domain: str, role: str = "founder") -> dict | None:
    """Search Hunter.io for emails by domain."""
    api_key = os.environ.get("HUNTER_API_KEY")
    if not api_key:
        return None
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={api_key}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ai-job-search/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  [!] Hunter.io error: {e}", file=sys.stderr)
        return None
    emails = data.get("data", {}).get("emails", [])
    if not emails:
        return None
    # Filter by role/person
    role_lower = role.lower()
    for e in emails:
        first_name = (e.get("first_name") or "").lower()
        last_name = (e.get("last_name") or "").lower()
        position = (e.get("position") or "").lower()
        if role_lower in position or role_lower in first_name or "founder" in position or "ceo" in position or "cto" in position:
            return {
                "email": e["value"],
                "name": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip(),
                "title": e.get("position", ""),
                "source": "hunter",
                "confidence": e.get("confidence", 0),
            }
    # Return first email if no role match
    if emails:
        e = emails[0]
        return {
            "email": e["value"],
            "name": f"{e.get('first_name', '')} {e.get('last_name', '')}".strip(),
            "title": e.get("position", ""),
            "source": "hunter",
            "confidence": e.get("confidence", 0),
        }
    return None


def find_email_apollo(domain: str, role: str = "founder") -> dict | None:
    """Search Apollo.io for contact emails by domain."""
    api_key = os.environ.get("APOLLO_API_KEY")
    if not api_key:
        return None
    url = "https://api.apollo.io/v1_mixed_people/search"
    payload = json.dumps({
        "q_organization_domains": [domain],
        "person_titles": [role, "founder", "ceo", "cto", "co-founder"],
        "per_page": 5,
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-API-KEY": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  [!] Apollo.io error: {e}", file=sys.stderr)
        return None
    people = data.get("people", [])
    for person in people:
        emails = person.get("email", "")
        if emails:
            return {
                "email": emails if isinstance(emails, str) else emails[0],
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "title": person.get("title", ""),
                "source": "apollo",
                "confidence": 80,
            }
    return None


def guess_email_pattern(domain: str, name: str | None = None) -> dict | None:
    """Guess email from common patterns (low accuracy, free)."""
    patterns = [f"founder@{domain}", f"hello@{domain}", f"team@{domain}", f"hi@{domain}"]
    if name:
        clean = name.lower().strip()
        first = clean.split()[0] if clean else ""
        last = clean.split()[-1] if len(clean.split()) > 1 else ""
        patterns.extend([
            f"{first}@{domain}",
            f"{first}.{last}@{domain}",
            f"{first[0]}{last}@{domain}",
        ])
    # Return the first pattern as a guess (caller should verify)
    return {
        "email": patterns[0],
        "name": name or "",
        "title": "unknown",
        "source": "pattern-guess",
        "confidence": 10,
    }


def verify_email_hunter(email: str) -> bool:
    """Verify an email address via Hunter.io."""
    api_key = os.environ.get("HUNTER_API_KEY")
    if not api_key:
        return False
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={api_key}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ai-job-search/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception:
        return False
    status = data.get("data", {}).get("status", "")
    return status in ("valid", "accept_all", "webmail")


def find_email(domain: str, role: str = "founder", verify: bool = False) -> dict | None:
    """Find the best email for a founder/CTO at a company domain.

    Tries: Hunter.io → Apollo.io → pattern guessing.
    Optionally verifies the email via Hunter.
    """
    result = None
    # 1. Try Hunter.io
    result = find_email_hunter(domain, role)
    if result and result.get("confidence", 0) >= 70:
        if verify and not verify_email_hunter(result["email"]):
            result["email_valid"] = False
        elif verify:
            result["email_valid"] = True
        return result
    # 2. Try Apollo.io
    result = find_email_apollo(domain, role)
    if result:
        if verify and os.environ.get("HUNTER_API_KEY"):
            result["email_valid"] = verify_email_hunter(result["email"])
        return result
    # 3. Fallback: pattern guessing
    result = guess_email_pattern(domain)
    if verify:
        result["email_valid"] = False
    return result


def main():
    ap = argparse.ArgumentParser(description="Find founder/CTO emails by company domain")
    ap.add_argument("--domain", required=True, help="Company domain (e.g., acme.io)")
    ap.add_argument("--role", default="founder", help="Role to search for (founder, cto, ceo)")
    ap.add_argument("--verify", action="store_true", help="Verify email via Hunter.io")
    ap.add_argument("--format", choices=["json", "plain"], default="json")
    args = ap.parse_args()

    result = find_email(args.domain, args.role, args.verify)
    if not result:
        print(json.dumps({"error": "no email found", "domain": args.domain}, indent=2))
        sys.exit(1)

    if args.format == "plain":
        print(result["email"])
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
