#!/usr/bin/env python3
"""Unified batch email sender with integrated dedup + bounce checking.

Prevents sending to:
  - Already-contacted emails
  - Known-bounced emails

Usage:
  python scripts/send_unified.py --to email@domain.com --subject "Subject" --body "Body" --company "Company"
  python scripts/send_unified.py --dry-run ...  # Check without sending
"""
import argparse
import json
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
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

SENDER = os.environ.get("GMAIL_SENDER", "you@example.com")
PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

DATA_DIR = Path(__file__).parent.parent / "data"
CONTACTED_FILE = DATA_DIR / "contacted_emails.json"
BOUNCED_FILE = DATA_DIR / "bounced_emails.json"
BASE = Path(__file__).parent.parent
CV_DIR = BASE / "cv"
COVER_DIR = BASE / "cover_letters"


def load_set(path: Path) -> set[str]:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_set(path: Path, data: set[str]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(data), f, indent=2, ensure_ascii=False)


def dedup_check(email: str) -> tuple[bool, str]:
    """Check if email can be sent. Returns (ok, reason)."""
    email = email.lower().strip()
    contacted = load_set(CONTACTED_FILE)
    bounced = load_set(BOUNCED_FILE)

    if email in bounced:
        return False, f"BOUNCED - {email} previously bounced"
    if email in contacted:
        return False, f"CONTACTED - {email} was already contacted"
    return True, "OK"


def send_email(to_email: str, subject: str, body: str,
               cv_path: Path = None, cover_path: Path = None) -> bool:
    """Send email with attachments."""
    msg = MIMEMultipart()
    msg["From"] = SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    for p in [cv_path, cover_path]:
        if p and p.exists():
            with open(p, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={p.name}")
            msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(SENDER, PASSWORD)
        server.send_message(msg)

    # Add to contacted
    contacted = load_set(CONTACTED_FILE)
    contacted.add(to_email.lower().strip())
    save_set(CONTACTED_FILE, contacted)
    return True


def main():
    ap = argparse.ArgumentParser(description="Unified sender with dedup")
    ap.add_argument("--to", required=True, help="Recipient email")
    ap.add_argument("--subject", required=True, help="Email subject")
    ap.add_argument("--body", required=True, help="Email body")
    ap.add_argument("--company", required=True, help="Company name (for tracking)")
    ap.add_argument("--cv", help="Path to CV PDF")
    ap.add_argument("--cover", help="Path to cover letter PDF")
    ap.add_argument("--dry-run", action="store_true", help="Check without sending")
    args = ap.parse_args()

    # Dedup check
    ok, reason = dedup_check(args.to)
    if not ok:
        print(f"SKIP: {reason}")
        sys.exit(1)

    if args.dry_run:
        print(f"DRY RUN: Would send to {args.to}")
        print(f"  Subject: {args.subject}")
        print(f"  Company: {args.company}")
        return

    cv_path = Path(args.cv) if args.cv else None
    cover_path = Path(args.cover) if args.cover else None

    try:
        send_email(args.to, args.subject, args.body, cv_path, cover_path)
        print(f"SENT: {args.company} -> {args.to}")
    except Exception as e:
        print(f"FAILED: {args.company} -> {args.to}: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
