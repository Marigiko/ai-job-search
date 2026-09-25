#!/usr/bin/env python3
"""Dedup + bounce tracking for job applications.

Tracks:
  - contacted_emails.json: emails already contacted (set)
  - bounced_emails.json: emails that bounced (set)

Usage:
  python scripts/dedup.py --check <email>
  python scripts/dedup.py --add <email>
  python scripts/dedup.py --bounce <email>
  python scripts/dedup.py --list
  python scripts/dedup.py --list-bounced
  python scripts/dedup.py --is-bounced <email>
  python scripts/dedup.py --stats
  python scripts/dedup.py --init-from-tracker
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CONTACTED_FILE = DATA_DIR / "contacted_emails.json"
BOUNCED_FILE = DATA_DIR / "bounced_emails.json"


def load_json(path: Path) -> set[str]:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_json(path: Path, data: set[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(data), f, indent=2, ensure_ascii=False)


def init_tracker():
    """Initialize contacted set from job_search_tracker.csv."""
    tracker = Path(__file__).parent.parent / "job_search_tracker.csv"
    contacted = load_json(CONTACTED_FILE)
    if tracker.exists():
        with open(tracker, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Try to find the mailto URL - it might be in different columns
                # due to CSV parsing issues with commas in notes
                mailto = None
                for key in ["application_url", "relocation_visa", "salary_offered"]:
                    val = row.get(key, "")
                    if val and "mailto:" in val.lower():
                        mailto = val.split("mailto:")[-1].strip().split()[0].strip().lower()
                        break

                if mailto:
                    contacted.add(mailto)

                # Also check notes field for embedded emails
                notes = row.get("notes", "")
                emails_in_notes = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', notes)
                for e in emails_in_notes:
                    if "linkedin" not in e.lower() and "indeed" not in e.lower():
                        contacted.add(e.lower())

    save_json(CONTACTED_FILE, contacted)
    print(f"Initialized {len(contacted)} contacted emails from tracker")


def main():
    ap = argparse.ArgumentParser(description="Dedup + bounce tracking")
    ap.add_argument("--check", help="Check if email was already contacted")
    ap.add_argument("--add", help="Add email to contacted set")
    ap.add_argument("--bounce", help="Add email to bounced set")
    ap.add_argument("--list", action="store_true", help="List contacted emails")
    ap.add_argument("--list-bounced", action="store_true", help="List bounced emails")
    ap.add_argument("--is-bounced", help="Check if email has bounced")
    ap.add_argument("--stats", action="store_true", help="Show stats")
    ap.add_argument("--init-from-tracker", action="store_true")
    args = ap.parse_args()

    contacted = load_json(CONTACTED_FILE)
    bounced = load_json(BOUNCED_FILE)

    if args.init_from_tracker:
        init_tracker()
        return

    if args.check:
        email = args.check.lower().strip()
        if email in bounced:
            print(f"BOUNCED - {email} previously bounced")
            sys.exit(2)
        elif email in contacted:
            print(f"CONTACTED - {email} was already contacted")
            sys.exit(0)
        else:
            print(f"NEW - {email} not yet contacted")
            sys.exit(1)

    if args.add:
        email = args.add.lower().strip()
        contacted.add(email)
        save_json(CONTACTED_FILE, contacted)
        print(f"Added {email} to contacted (total: {len(contacted)})")

    if args.bounce:
        email = args.bounce.lower().strip()
        bounced.add(email)
        save_json(BOUNCED_FILE, bounced)
        print(f"Added {email} to bounced (total: {len(bounced)})")

    if args.list:
        for e in sorted(contacted):
            marker = " [BOUNCED]" if e in bounced else ""
            print(f"  {e}{marker}")
        print(f"\nTotal contacted: {len(contacted)}")

    if args.list_bounced:
        for e in sorted(bounced):
            print(f"  {e}")
        print(f"\nTotal bounced: {len(bounced)}")

    if args.is_bounced:
        email = args.is_bounced.lower().strip()
        if email in bounced:
            print(f"YES - {email} has bounced")
            sys.exit(0)
        else:
            print(f"NO - {email} has not bounced")
            sys.exit(1)

    if args.stats:
        print(f"Contacted: {len(contacted)}")
        print(f"Bounced:   {len(bounced)}")
        print(f"Valid:     {len(contacted - bounced)}")
        bounced_in_contacted = contacted & bounced
        if bounced_in_contacted:
            print(f"\nBounced but still in contacted:")
            for e in sorted(bounced_in_contacted):
                print(f"  {e}")


if __name__ == "__main__":
    main()
