#!/usr/bin/env python3
"""Semi-automatic outreach sender.

Reads leads from data/leads.csv, generates personalized cold emails to startup
founders using A/B tested templates, shows preview for manual approval, sends with
rate limiting.

Usage:
  python scripts/outreach_sender.py --dry-run          # Preview without sending
  python scripts/outreach_sender.py --send             # Preview + send approved
  python scripts/outreach_sender.py --dry-run --limit 3  # Preview top 3 leads
  python scripts/outreach_sender.py --send --template ab  # Use A/B template selector
"""
import argparse
import csv
import os
import random
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from env_loader import load_env
load_env()

# Import A/B template system
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ab_templates import select_template, cmd_record

LEADS_CSV = Path(__file__).parent.parent / "data" / "leads.csv"
SENDER = os.getenv("GMAIL_SENDER", "you@example.com")

# Legacy default template (used when --template legacy)
OUTBOUND_SUBJECT = "{company} — founding engineer interest"
OUTBOUND_TEMPLATE = """Hi {founder_name},

I'm Mario, a full-stack dev from Argentina. I've been following {company} since {trigger}.

I specialize in building MVPs fast (shipped products in <72h at my last role) and AI automation (reduced ops friction significantly at a YC-backed startup).

I'm looking for a founding engineer role at a US startup like yours. I can start at $1K/mo to prove value — then we discuss equity.

Open to a 15-min call this week?

Best,
Mario Aquino
linkedin.com/in/keyzdev · github.com/Marigiko
"""

CSV_FIELDS = [
    "id", "company", "role", "source", "url", "email", "email_source",
    "status", "date_found", "date_contacted", "response", "notes",
]


def load_leads(status_filter: str = "enriched") -> list[dict]:
    """Load leads from CSV, optionally filtered by status."""
    if not LEADS_CSV.exists():
        print(f"[!] {LEADS_CSV} not found. Run discovery first.")
        return []
    leads = []
    with open(LEADS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not status_filter or row.get("status") == status_filter:
                leads.append(row)
    return leads


def generate_email(lead: dict, use_ab: bool = True) -> tuple[str, str, str | None]:
    """Generate personalized email for a lead. Returns (subject, body, template_id)."""
    company = lead.get("company", "your startup")
    founder_name = lead.get("founder_name", "")
    if not founder_name:
        founder_name = "there"
    trigger = lead.get("notes", "your recent launch")
    if not trigger or trigger == "your recent launch":
        trigger = "seeing what you're building"

    if use_ab:
        template_id, tmpl = select_template("best")
        subject = tmpl["subject"].format(
            company=company, founder_name=founder_name, trigger=trigger,
        )
        body = tmpl["body"].format(
            company=company, founder_name=founder_name, trigger=trigger,
        )
        return subject, body, template_id

    # Legacy template
    subject = OUTBOUND_SUBJECT.format(company=company)
    body = OUTBOUND_TEMPLATE.format(
        founder_name=founder_name, company=company, trigger=trigger,
    )
    return subject, body, None


def send_email(to_email: str, subject: str, body: str, cv_path: str | None = None) -> bool:
    """Send email via Gmail SMTP."""
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not password:
        raise ValueError("GMAIL_APP_PASSWORD not set in .env")
    msg = MIMEMultipart()
    msg["From"] = SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    if cv_path and Path(cv_path).exists():
        with open(cv_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={Path(cv_path).name}")
        msg.attach(part)
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(SENDER, password)
        server.send_message(msg)
    return True


def update_lead_status(lead_id: str, new_status: str, date_contacted: str | None = None):
    """Update a lead's status in the CSV."""
    if not LEADS_CSV.exists():
        return
    rows = []
    with open(LEADS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"] == lead_id:
                row["status"] = new_status
                if date_contacted:
                    row["date_contacted"] = date_contacted
            rows.append(row)
    with open(LEADS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description="Semi-automatic outreach sender")
    ap.add_argument("--dry-run", action="store_true", help="Preview emails without sending")
    ap.add_argument("--send", action="store_true", help="Preview + send approved emails")
    ap.add_argument("--limit", type=int, default=5, help="Max leads to process (default 5)")
    ap.add_argument("--max-per-day", type=int, default=5, help="Daily send cap (default 5)")
    ap.add_argument("--delay-min", type=int, default=30, help="Min delay between emails in minutes")
    ap.add_argument("--cv", type=str, help="Path to CV PDF to attach")
    ap.add_argument("--template", choices=["ab", "legacy"], default="ab", help="Template mode: ab (A/B tested) or legacy")
    args = ap.parse_args()

    if not args.dry_run and not args.send:
        print("Specify --dry-run (preview only) or --send (preview + send approved)")
        sys.exit(1)

    use_ab = args.template == "ab"

    leads = load_leads("enriched")
    if not leads:
        print("No leads with status=enriched found. Run discovery first.")
        sys.exit(0)

    leads = leads[: args.limit]
    print(f"\n{'='*60}")
    print(f"OUTREACH BATCH — {len(leads)} leads")
    print(f"Mode: {'DRY RUN (preview only)' if args.dry_run else 'SEND (with approval)'}")
    print(f"{'='*60}\n")

    sent_today = 0
    for i, lead in enumerate(leads, 1):
        company = lead.get("company", "Unknown")
        email = lead.get("email", "")
        if not email:
            print(f"[{i}/{len(leads)}] SKIP {company} — no email")
            continue

        subject, body, template_id = generate_email(lead, use_ab)
        print(f"\n{'─'*50}")
        print(f"[{i}/{len(leads)}] To: {email} ({company})")
        if template_id:
            print(f"  Template: {template_id}")
        print(f"Subject: {subject}")
        print(f"{'─'*50}")
        print(body[:300] + "..." if len(body) > 300 else body)

        if args.dry_run:
            print(f"  → DRY RUN (not sent)")
            continue

        # Send mode: ask approval
        if sent_today >= args.max_per_day:
            print(f"  → DAILY CAP REACHED ({args.max_per_day})")
            break

        print(f"\nSend this email? [y/N/q] ", end="", flush=True)
        try:
            answer = input().strip().lower()
        except EOFError:
            answer = "n"
        if answer == "q":
            print("  → Quit")
            break
        if answer != "y":
            print(f"  → Skipped")
            continue

        try:
            send_email(email, subject, body, args.cv)
            update_lead_status(lead["id"], "contacted", time.strftime("%Y-%m-%d"))
            if template_id:
                cmd_record(template_id, company, "sent")
            sent_today += 1
            print(f"  ✓ Sent ({sent_today}/{args.max_per_day} today)")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue

        # Rate limiting delay (skip after last email)
        if i < len(leads) and sent_today < args.max_per_day:
            delay = random.randint(args.delay_min * 60, args.delay_min * 60 * 4)  # seconds
            print(f"  ⏳ Waiting {delay // 60}m {delay % 60}s before next email...")
            time.sleep(delay)

    print(f"\n{'='*60}")
    print(f"DONE — {sent_today} emails sent")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
