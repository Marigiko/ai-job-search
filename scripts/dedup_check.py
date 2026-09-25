#!/usr/bin/env python3
"""Dedup tracking for job applications.

Maintains a set of already-contacted emails to prevent duplicate sends.
Usage:
  python scripts/dedup_check.py --check <email@domain.com>
  python scripts/dedup_check.py --add <email@domain.com>
  python scripts/dedup_check.py --list
  python scripts/dedup_check.py --export  # prints all emails as Python set
"""
import argparse
import json
import sys
from pathlib import Path

DEDUP_FILE = Path(__file__).parent.parent / "data" / "contacted_emails.json"


def load() -> set[str]:
    if DEDUP_FILE.exists():
        with open(DEDUP_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save(emails: set[str]):
    DEDUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DEDUP_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(emails), f, indent=2, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description="Dedup tracking for job applications")
    ap.add_argument("--check", help="Check if email was already contacted")
    ap.add_argument("--add", help="Add email to contacted set")
    ap.add_argument("--list", action="store_true", help="List all contacted emails")
    ap.add_argument("--export", action="store_true", help="Export as Python set")
    ap.add_argument("--init-from-tracker", action="store_true",
                    help="Initialize from job_search_tracker.csv")
    args = ap.parse_args()

    emails = load()

    if args.init_from_tracker:
        # Initialize from existing tracker
        import csv
        tracker = Path(__file__).parent.parent / "job_search_tracker.csv"
        if tracker.exists():
            with open(tracker, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get("application_url", "")
                    if url.startswith("mailto:"):
                        email = url.replace("mailto:", "").strip()
                        emails.add(email.lower())
            save(emails)
            print(f"Initialized {len(emails)} emails from tracker")
        else:
            print("Tracker file not found")
        return

    if args.check:
        email = args.check.lower().strip()
        if email in emails:
            print(f"YES - {email} was already contacted")
            sys.exit(0)
        else:
            print(f"NO - {email} not yet contacted")
            sys.exit(1)

    if args.add:
        email = args.add.lower().strip()
        emails.add(email)
        save(emails)
        print(f"Added {email} (total: {len(emails)})")

    if args.list:
        for e in sorted(emails):
            print(f"  {e}")
        print(f"\nTotal: {len(emails)} emails")

    if args.export:
        print(repr(emails))


if __name__ == "__main__":
    main()
