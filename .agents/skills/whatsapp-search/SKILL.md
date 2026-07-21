---
name: whatsapp-search
version: 1.0.0
description: >
  Use this skill to fetch and parse job postings from WhatsApp groups. Uses Baileys
  (WhatsApp Web protocol) to read messages from groups the linked account is in. Session
  persisted via QR scan. Extracted postings feed the /apply workflow. Personal use only
  (WhatsApp ToS — ban risk). Trigger phrases: whatsapp jobs, whatsapp group jobs, fetch
  whatsapp, whatsapp vacancies, trabajos whatsapp.
context: fork
allowed-tools: Bash(bun run .agents/skills/whatsapp-search/cli/src/cli.ts *)
---

# WhatsApp Job Search Skill

Fetch job postings from WhatsApp groups using Baileys (WhatsApp Web protocol).

## When to use

- The user wants to check job offers in their WhatsApp groups
- The user says "fetch whatsapp", "check whatsapp jobs"

## Commands

### Authenticate (QR scan — one-time)

```bash
bun run .agents/skills/whatsapp-search/cli/src/cli.ts auth
```

### Fetch messages from groups

```bash
bun run .agents/skills/whatsapp-search/cli/src/cli.ts fetch \
  [--limit 50] [--format json]
```

### Listen for new messages (real-time)

```bash
bun run .agents/skills/whatsapp-search/cli/src/cli.ts listen \
  [--groups "group1,group2"]
```

### Parse a pasted WhatsApp message

```bash
bun run .agents/skills/whatsapp-search/cli/src/cli.ts parse --text "pasted text"
```

## Session storage

Session credentials stored in `job_scraper/.whatsapp_session/` (gitignored).

## Output contract

`fetch` and `listen` emit `{ "meta": { "count" }, "results": [...] }`. Each result has
`id, title, company, location, date, url, applyEmail, author, text, source: "whatsapp"`.

Errors go to **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.

## Warnings

- **Ban risk**: WhatsApp detects and bans unofficial API use. Use a secondary number.
- **QR session**: Must re-scan if the phone changes or session expires.
- **ToS violation**: Automated access is against WhatsApp's Terms of Service.
