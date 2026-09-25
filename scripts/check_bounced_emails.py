#!/usr/bin/env python3
"""Check Gmail Inbox + Trash for bounced emails (delivery status notifications).

Connects to Gmail via IMAP, searches for delivery status notifications,
and reports which recipient emails bounced.
"""
import email
import imaplib
import os
import re
import sys
from email.header import decode_header
from pathlib import Path

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

if not PASSWORD:
    print("ERROR: GMAIL_APP_PASSWORD not set in .env")
    sys.exit(1)

def decode_mime_header(header_value):
    if not header_value:
        return ""
    parts = decode_header(header_value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)

def extract_bounced_email(body):
    """Extract the bounced recipient email from DSN body."""
    patterns = [
        r"Final-Recipient:[^<]*<([^>]+)>",
        r"Original-Recipient:[^<]*<([^>]+)>",
        r"failed\s+permanently[^<]*<([^>]+)>",
        r"Delivery\s+to\s+the\s+following\s+recipient\s+failed[^<]*<([^>]+)>",
        r"action:\s*failed[^<]*<([^>]+)>",
        r"<([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>",
    ]
    for pat in patterns:
        m = re.search(pat, body, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).lower()
    return None

def collect_bounced(mail, msg_ids_list):
    bounced_list = []
    for msg_id in msg_ids_list:
        status, msg_data = mail.fetch(msg_id, "(RFC822)")
        if status != "OK":
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        subject = decode_mime_header(msg.get("Subject", ""))
        from_addr = decode_mime_header(msg.get("From", ""))
        date = msg.get("Date", "")
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    body = part.get_payload(decode=True).decode(charset, errors="replace")
                    break
        else:
            charset = msg.get_content_charset() or "utf-8"
            body = msg.get_payload(decode=True).decode(charset, errors="replace")
        bounced_email = extract_bounced_email(body)
        if bounced_email:
            bounced_list.append({
                "bounced_email": bounced_email,
                "subject": subject[:80],
                "from": from_addr[:50],
                "date": date[:30],
            })
    return bounced_list

def main():
    print(f"Connecting to Gmail as {SENDER}...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(SENDER, PASSWORD)

    all_bounced = []

    # Search Inbox
    print("\n=== Checking INBOX ===")
    status, _ = mail.select("INBOX")
    if status == "OK":
        status, messages = mail.search(None, '(SUBJECT "Delivery Status Notification")')
        if status == "OK" and messages[0]:
            msg_ids = messages[0].split()
            print(f"Found {len(msg_ids)} DSN emails in Inbox.")
            all_bounced.extend(collect_bounced(mail, msg_ids))
        else:
            # Try broader search
            status, messages = mail.search(None, '(OR SUBJECT "Undelivered" SUBJECT "Returned" SUBJECT "failure" SUBJECT "Mail Delivery Subsystem")')
            if status == "OK" and messages[0]:
                msg_ids = messages[0].split()
                print(f"Found {len(msg_ids)} bounce-related emails in Inbox.")
                all_bounced.extend(collect_bounced(mail, msg_ids))
            else:
                print("No bounced emails found in Inbox.")

    # Search Trash
    print("\n=== Checking TRASH ===")
    status, folders = mail.list()
    trash_folder = "[Gmail]/Papelera"
    if status == "OK":
        for folder in folders:
            decoded = folder.decode() if isinstance(folder, bytes) else str(folder)
            if "Trash" in decoded or "Bin" in decoded or "Papelera" in decoded:
                parts = decoded.split(' "/" ')
                if len(parts) >= 2:
                    trash_folder = parts[-1].strip('"')
                    break

    status, _ = mail.select(trash_folder)
    if status != "OK":
        mail.select("[Gmail]/Trash")
        trash_folder = "[Gmail]/Trash"

    status, messages = mail.search(None, '(SUBJECT "Delivery Status Notification")')
    if status == "OK" and messages[0]:
        msg_ids = messages[0].split()
        print(f"Found {len(msg_ids)} DSN emails in Trash.")
        all_bounced.extend(collect_bounced(mail, msg_ids))
    else:
        status, messages = mail.search(None, '(OR SUBJECT "Undelivered" SUBJECT "Returned" SUBJECT "failure")')
        if status == "OK" and messages[0]:
            msg_ids = messages[0].split()
            print(f"Found {len(msg_ids)} bounce-related emails in Trash.")
            all_bounced.extend(collect_bounced(mail, msg_ids))
        else:
            print("No bounced emails found in Trash.")

    mail.logout()

    # Deduplicate by bounced email
    seen = set()
    unique_bounced = []
    for b in all_bounced:
        if b["bounced_email"] not in seen:
            seen.add(b["bounced_email"])
            unique_bounced.append(b)

    if unique_bounced:
        print(f"\n{'='*60}")
        print(f"BOUNCED EMAILS FOUND: {len(unique_bounced)}")
        print(f"{'='*60}")
        for b in unique_bounced:
            print(f"\n  Bounced: {b['bounced_email']}")
            print(f"  Subject: {b['subject']}")
            print(f"  From:    {b['from']}")
            print(f"  Date:    {b['date']}")
    else:
        print("\nNo bounced emails found.")


if __name__ == "__main__":
    main()
