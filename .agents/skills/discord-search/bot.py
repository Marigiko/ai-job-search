#!/usr/bin/env python3
"""Discord bot fetcher — read job postings from Discord channels via discord.py.

Called by the bun CLI wrapper (`cli/src/cli.ts`).
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

TOKEN = os.getenv("DISCORD_BOT_TOKEN")


def write_error(msg: str, code: str) -> None:
    sys.stderr.write(json.dumps({"error": msg, "code": code}) + "\n")


def write_output(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _parse_message(content: str, author: str | None, msg_id: int, created_at: str) -> dict | None:
    from sources.discord_source import parse
    if not content.strip():
        return None
    parsed = parse(content)
    parsed["id"] = str(msg_id)
    parsed["date"] = created_at
    parsed["author"] = author
    parsed["source"] = "discord"
    return parsed


def _get_intents():
    import discord
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    intents.guilds = True
    return intents


async def fetch_channel(args: argparse.Namespace) -> int:
    import discord
    if not TOKEN:
        write_error("DISCORD_BOT_TOKEN required", "NO_AUTH")
        return 1
    client = discord.Client(intents=_get_intents())
    results = []

    @client.event
    async def on_ready():
        channel = None
        for guild in client.guilds:
            channel = discord.utils.get(guild.text_channels, name=args.channel)
            if channel:
                break
        if not channel:
            write_error(f"channel '{args.channel}' not found in any guild", "NO_CHANNEL")
            await client.close()
            return
        limit = args.limit or 50
        async for msg in channel.history(limit=limit):
            parsed = _parse_message(msg.content, str(msg.author), msg.id, msg.created_at.isoformat())
            if parsed and (parsed.get("apply_email") or parsed.get("title")):
                results.append(parsed)
        write_output({"meta": {"count": len(results), "channel": args.channel}, "results": results})
        await client.close()

    try:
        await client.start(TOKEN)
    except Exception as e:
        write_error(str(e), "FETCH_FAILED")
        return 1
    return 0


async def list_channels(args: argparse.Namespace) -> int:
    import discord
    if not TOKEN:
        write_error("DISCORD_BOT_TOKEN required", "NO_AUTH")
        return 1
    client = discord.Client(intents=_get_intents())
    results = []

    @client.event
    async def on_ready():
        for guild in client.guilds:
            for channel in guild.text_channels:
                results.append(
                    {
                        "guild": guild.name,
                        "channel": channel.name,
                        "id": channel.id,
                    }
                )
        write_output({"meta": {"count": len(results)}, "results": results})
        await client.close()

    try:
        await client.start(TOKEN)
    except Exception as e:
        write_error(str(e), "LIST_FAILED")
        return 1
    return 0


async def listen_channels(args: argparse.Namespace) -> int:
    import discord
    if not TOKEN:
        write_error("DISCORD_BOT_TOKEN required", "NO_AUTH")
        return 1
    client = discord.Client(intents=_get_intents())
    channels_filter = [c.strip() for c in (args.channels or "").split(",") if c.strip()]

    @client.event
    async def on_message(msg):
        if msg.author.bot:
            return
        if channels_filter and msg.channel.name not in channels_filter:
            return
        parsed = _parse_message(msg.content, str(msg.author), msg.id, msg.created_at.isoformat())
        if parsed and (parsed.get("apply_email") or parsed.get("title")):
            write_output({"event": "new_job", "result": parsed})

    write_output({"status": "listening", "channels": channels_filter or "all", "message": "Press Ctrl+C to stop."})
    try:
        await client.start(TOKEN)
    except Exception as e:
        write_error(str(e), "LISTEN_FAILED")
        return 1
    return 0


async def cmd_parse(args: argparse.Namespace) -> int:
    from sources.discord_source import parse
    result = parse(args.text)
    result["source"] = "discord"
    write_output(result)
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Discord job fetcher")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch")
    p_fetch.add_argument("--channel", required=True)
    p_fetch.add_argument("--limit", type=int, default=50)

    p_listen = sub.add_parser("listen")
    p_listen.add_argument("--channels", default="")

    p_parse = sub.add_parser("parse")
    p_parse.add_argument("--text", required=True)

    sub.add_parser("channels")

    args = ap.parse_args()
    if args.cmd == "parse":
        sys.exit(asyncio.run(cmd_parse(args)))
    if args.cmd == "fetch":
        sys.exit(asyncio.run(fetch_channel(args)))
    if args.cmd == "channels":
        sys.exit(asyncio.run(list_channels(args)))
    if args.cmd == "listen":
        sys.exit(asyncio.run(listen_channels(args)))


if __name__ == "__main__":
    main()
