---
name: discord-search
version: 1.0.0
description: >
  Use this skill to fetch and parse job postings from Discord channels. Uses discord.py
  bot to read messages from channels the bot has access to. Extracted postings feed the
  /apply workflow. Trigger phrases: discord jobs, discord job channel, fetch discord,
  discord vacancies, trabajos discord, discord hiring.
context: fork
allowed-tools: Bash(bun run .agents/skills/discord-search/cli/src/cli.ts *), Bash(python3 .agents/skills/discord-search/bot.py *)
---

# Discord Job Search Skill

Fetch job postings from Discord channels using a discord.py bot.

## When to use

- The user wants to check job offers in their Discord channels
- The user says "fetch discord", "check discord jobs", "discord vacancies"
- As part of `/scrape` to pull from Discord

## Commands

### Fetch jobs from a channel

```bash
bun run .agents/skills/discord-search/cli/src/cli.ts fetch \
  --channel "jobs" [--limit 50] [--format json|plain]
```

### List guilds + channels the bot can see

```bash
bun run .agents/skills/discord-search/cli/src/cli.ts channels
```

### Listen for new messages (real-time)

```bash
bun run .agents/skills/discord-search/cli/src/cli.ts listen --channels "jobs,careers"
```

### Parse a single pasted Discord message

```bash
bun run .agents/skills/discord-search/cli/src/cli.ts parse --text "pasted text"
```

## Environment variables

| Var | Source |
|-----|--------|
| `DISCORD_BOT_TOKEN` | https://discord.com/developers/applications → Bot → Token |
| `DISCORD_INTENTS` | Set to `message_content,guilds,messages` (default) |

Bot must be invited to the server with `Read Messages` and `Read Message History` permissions.

Enabling `message_content` intent requires verification for bots in 100+ servers.

## Output contract

`fetch` emits `{ "meta": { "count" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url, applyEmail, author, text, source`, plus
`source: "discord"`.

Errors go to **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.
