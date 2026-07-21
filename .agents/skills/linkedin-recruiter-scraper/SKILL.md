---
name: linkedin-recruiter-scraper
version: 1.0.0
description: >
  Use this skill to discover LinkedIn recruiter POSTS that contain apply-by-email
  addresses for a given role/location. Searches public search engines (Google/Bing)
  via Playwright/chromium to find LinkedIn post permalinks, then extracts the apply
  email + metadata from each. Designed to feed the email application workflow
  (`/apply` with `applyEmail`). Personal use only (LinkedIn ToS) — no authentication,
  no feed crawling. Trigger phrases: linkedin recruiter posts, linkedin email jobs,
  scrape linkedin posts, find linkedin hiring posts, linkedin post scraper.
context: fork
allowed-tools: Bash(bun --version), Bash(bun run .agents/skills/linkedin-recruiter-scraper/cli/src/cli.ts *)
---

# LinkedIn Recruiter Post Scraper

Discover LinkedIn recruiter posts with apply-by-email addresses — **without
authenticating against LinkedIn**. Uses **public search engines** (Google/Bing) to
find `linkedin.com/posts/...` permalinks, then extracts the apply email + metadata
from each post. The bridge to the **email application workflow** (`/apply` with
`applyEmail`).

## When to use

- The user wants to find recruiter posts for a role (e.g. "backend developer remote")
- The user has search queries and wants apply-by-email leads
- As discovery step before `linkedin_email_workflow.py` / `/apply`
- The user says "scrape linkedin posts", "linkedin recruiter posts", "find linkedin email jobs"

## Architecture

```
queries.txt ──► cli.ts search (Playwright+Google/Bing) ──► LinkedIn URLs
                                                          │
                  cli.ts extract (per URL) ◄───────────────┘
                                │
                                ▼
                      { meta: { count }, results: [...] }
                      (url, company, title, applyEmail, date, ...)
```

## Commands

### Search for recruiter posts (discovery — Playwright required)

```bash
bun run .agents/skills/linkedin-recruiter-scraper/cli/src/cli.ts search \
  --query "site:linkedin.com/posts hiring backend developer email" \
  [--max-results 5] [--engine google|bing]
```

Flags:
- `--query <text>` / `-q <text>` — search query. Use `site:linkedin.com/posts` restriction.
- `--max-results <n>` / `-m <n>` — max LinkedIn posts per query (default 5).
- `--engine <name>` / `-e <name>` — `google` or `bing` (default `bing` — fewer CAPTCHAs).

### Extract from a known post URL

```bash
bun run .agents/skills/linkedin-recruiter-scraper/cli/src/cli.ts extract <post-url>
```

### Parse pasted post text (offline fallback)

```bash
bun run .agents/skills/linkedin-recruiter-scraper/cli/src/cli.ts parse --text "<post text>"
```

### Fetch full detail from a search result URL

```bash
bun run .agents/skills/linkedin-recruiter-scraper/cli/src/cli.ts detail <post-url>
# alias: extract
```

## Output contract

Search emits `{ "meta": { "count" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url, applyEmail, emails, author, text, source`
(missing values `null`), plus `source: "linkedin-recruiter-post"`.

All errors go to **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.

## Usage examples

```bash
# Search for backend developer hiring posts on bing (default)
bun run .agents/skills/linkedin-recruiter-scraper/cli/src/cli.ts search \
  --query "site:linkedin.com/posts hiring backend developer email" --format json

# AI developer posts, google engine, max 10
bun run .agents/skills/linkedin-recruiter-scraper/cli/src/cli.ts search \
  --query "site:linkedin.com/posts hiring AI developer LLM email" \
  --max-results 10 --engine google

# Extract from a known post URL
bun run .agents/skills/linkedin-recruiter-scraper/cli/src/cli.ts extract \
  "https://www.linkedin.com/posts/johndoe_hiring-backend-activity-7331931219363852288"

# Parse pasted text
bun run .agents/skills/linkedin-recruiter-scraper/cli/src/cli.ts parse \
  --text "Hiring backend! Send CV to jobs [at] company [dot] com"
```

## Notes

- **Playwright + chromium required** for `search` (browser automation). Install with:
  `bun install && npx playwright install chromium`. `extract` and `parse` do not need Playwright.
- `search` uses Bing by default — Google may intercept with CAPTCHA/consent, Bing is friendlier to automation.
- The post `date` is decoded from the activity id's high bits when available.
- `applyEmail` is the first address found; `emails` lists all.
- If a post has no email, the lead still carries the text/author so the user can apply via the normal channel.
- `format` flag is accepted but currently output is always JSON (standard contract).
