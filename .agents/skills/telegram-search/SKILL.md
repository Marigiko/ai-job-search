---
name: telegram-search
version: 1.0.0
description: >
  Use this skill to fetch and parse job postings from Telegram groups. Uses Telethon
  (MTProto user account) to read messages from groups the user is a member of — including
  history. Extracted postings feed the /apply workflow. Personal use only. Trigger
  phrases: telegram jobs, telegram group jobs, fetch telegram, telegram vacancies,
  trabajos telegram, telegram job offers.
context: fork
allowed-tools: Bash(bun run .agents/skills/telegram-search/cli/src/cli.ts *), Bash(python3 .agents/skills/telegram-search/fetcher.py *)
---

# Telegram Job Search Skill

Fetch job postings from Telegram groups using Telethon (MTProto user account).

## When to use

- The user wants to check job offers in their Telegram groups
- The user says "fetch telegram", "check telegram jobs", "telegram vacancies"
- As part of `/scrape` to pull from messaging platforms

## Commands

### Fetch jobs from a group

```bash
bun run .agents/skills/telegram-search/cli/src/cli.ts fetch \
  --group "Tech Jobs Argentina" [--limit 50] [--format json|plain]
```

### List groups/chats the account is in

```bash
bun run .agents/skills/telegram-search/cli/src/cli.ts dialogs [--limit 20]
```

### Listen for new job messages (real-time listener)

```bash
bun run .agents/skills/telegram-search/cli/src/cli.ts listen \
  --groups "group1,group2" [--format json]
```

### Parse a single pasted Telegram message

```bash
bun run .agents/skills/telegram-search/cli/src/cli.ts parse --text "pasteed text"
```

### Authenticate (one-time setup)

```bash
# Set env vars then run:
python3 .agents/skills/telegram-search/fetcher.py --auth
# or interactively:
bun run .agents/skills/telegram-search/cli/src/cli.ts auth
```

## Environment variables (stored in .env or exported)

| Var | Source |
|-----|--------|
| `TELEGRAM_API_ID` | https://my.telegram.org (My Applications) |
| `TELEGRAM_API_HASH` | https://my.telegram.org |
| `TELEGRAM_SESSION` | Path to .session file (default: `job_scraper/.telegram_session`) |

## Output contract

`fetch` and `listen` emit `{ "meta": { "count" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url, applyEmail, emails, author, text, source`
(missing values `null`), plus `source: "telegram"`.

All errors go to **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.

## Notes

- First run requires phone number verification (Telethon prompts interactively).
- Session persists in a `.session` file — no need to re-verify.
- Respect rate limits (1 second delay between fetches).
- MTProto user-account access is ToS-violating for mass scraping — keep volume moderate.
- The user must already be a member of the target groups.
