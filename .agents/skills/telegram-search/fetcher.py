#!/usr/bin/env python3
"""Telegram fetcher — read job postings from Telegram groups via Telethon.

Called by the bun CLI wrapper (`cli/src/cli.ts`). Handles auth, fetch, and listen modes.
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_DIR = Path(os.getenv("TELEGRAM_SESSION", "job_scraper"))
SESSION_DIR.mkdir(parents=True, exist_ok=True)
SESSION_PATH = SESSION_DIR / ".telegram_session"


def write_error(msg: str, code: str) -> None:
    sys.stderr.write(json.dumps({"error": msg, "code": code}) + "\n")


def write_output(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _get_client():
    from telethon import TelegramClient
    if not API_ID or not API_HASH:
        write_error(
            "TELEGRAM_API_ID and TELEGRAM_API_HASH required. Get them at https://my.telegram.org",
            "NO_AUTH",
        )
        sys.exit(1)
    return TelegramClient(str(SESSION_PATH), int(API_ID), API_HASH)


def _parse_message(msg) -> dict:
    from sources.telegram_source import parse
    text = msg.message or ""
    if not text:
        return None
    parsed = parse(text)
    parsed["id"] = str(msg.id)
    parsed["date"] = msg.date.isoformat() if msg.date else None
    parsed["author"] = getattr(msg.sender, "first_name", None) if msg.sender else None
    parsed["source"] = "telegram"
    return parsed


async def fetch_group(args: argparse.Namespace) -> int:
    client = _get_client()
    await client.start()
    try:
        group = await client.get_entity(args.group)
        messages = []
        limit = args.limit or 50
        async for msg in client.iter_messages(group, limit=limit):
            parsed = _parse_message(msg)
            if parsed and (parsed.get("apply_email") or parsed.get("title")):
                messages.append(parsed)
        write_output({"meta": {"count": len(messages), "group": args.group}, "results": messages})
        return 0
    except Exception as e:
        write_error(str(e), "FETCH_FAILED")
        return 1
    finally:
        await client.disconnect()


async def list_dialogs(args: argparse.Namespace) -> int:
    client = _get_client()
    await client.start()
    try:
        dialogs = []
        async for dialog in client.iter_dialogs(limit=args.limit or 20):
            if dialog.is_group or dialog.is_channel:
                dialogs.append(
                    {"id": dialog.entity.id, "title": dialog.name, "type": "group" if dialog.is_group else "channel"}
                )
        write_output({"meta": {"count": len(dialogs)}, "results": dialogs})
        return 0
    except Exception as e:
        write_error(str(e), "DIALOGS_FAILED")
        return 1
    finally:
        await client.disconnect()


async def listen_groups(args: argparse.Namespace) -> int:
    from telethon import events
    client = _get_client()
    await client.start()
    groups = [g.strip() for g in args.groups.split(",") if g.strip()]

    found = []

    @client.on(events.NewMessage(chats=groups if groups else None))
    async def handler(event):
        parsed = _parse_message(event.message)
        if parsed and (parsed.get("apply_email") or parsed.get("title")):
            parsed["event"] = "new_message"
            found.append(parsed)
            write_output({"event": "new_job", "result": parsed})

    write_output({"status": "listening", "groups": groups or "all", "message": "Press Ctrl+C to stop."})
    await client.run_until_disconnected()


async def cmd_auth() -> int:
    client = _get_client()
    await client.start()
    if await client.is_user_authorized():
        write_output({"status": "already_authorized", "session": str(SESSION_PATH)})
    else:
        write_error("Run interactively: python3 fetcher.py --auth", "NEEDS_INTERACTIVE")
        return 1
    await client.disconnect()
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Telegram job fetcher")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch")
    p_fetch.add_argument("--group", required=True)
    p_fetch.add_argument("--limit", type=int, default=50)

    p_dialogs = sub.add_parser("dialogs")
    p_dialogs.add_argument("--limit", type=int, default=20)

    p_listen = sub.add_parser("listen")
    p_listen.add_argument("--groups", default="")

    sub.add_parser("auth")

    args = ap.parse_args()

    if args.cmd == "auth":
        sys.exit(asyncio.run(cmd_auth()))
    if args.cmd == "fetch":
        sys.exit(asyncio.run(fetch_group(args)))
    if args.cmd == "dialogs":
        sys.exit(asyncio.run(list_dialogs(args)))
    if args.cmd == "listen":
        sys.exit(asyncio.run(listen_groups(args)))


if __name__ == "__main__":
    main()
