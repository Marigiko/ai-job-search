---
name: scrape
description: >
  Finds new job postings matching your profile via installed portal-search CLIs
  (LinkedIn, local job boards, and any skills added with /add-portal). Deduplicates
  across runs. Triggers on: job scrape, find jobs, search jobs, new jobs, job search,
  scrape jobs, /scrape
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(bun --version), Bash(bun run .agents/skills/*/cli/src/cli.ts *), Bash(python3 .agents/skills/*/scraper.py *), Bash(python3 .agents/skills/*/cli/src/cli.py *), Bash(python3 .agents/skills/image-ocr/cli/ocr_cli.py *), Bash(python3 .agents/skills/telegram-search/fetcher.py *), Bash(python3 .agents/skills/discord-search/bot.py *), WebFetch, WebSearch, Agent, AskUserQuestion
---

# Job Scraper

---

## How It Works

This skill searches job portals using the **installed portal-search CLIs** in
`.agents/skills/` (plus WebSearch as a fallback), using queries from your profile.
It deduplicates against previously seen jobs and the application tracker, and
presents new matches with a quick fit assessment.

## Invocation

The user triggers this skill by saying things like:
- "Find new jobs"
- "Scrape for jobs"
- "Any new positions?"
- "/scrape"

Optional arguments:
- A focus area, e.g. "/scrape data science" or "/scrape geophysics"
- "broad" to run all search categories, e.g. "/scrape broad"

---

## Execution Steps

### Step 0: Load State

1. Read `job_scraper/seen_jobs.json` (create if missing - start with `{"seen": {}}`)
2. Read `job_search_tracker.csv` to extract already-applied companies+roles
3. Read `search-queries.md` (this directory) for the search strategy

### Step 1: Search

Read `search-queries.md` (this directory) for the search strategy. By default, run the top 3 priority query categories. If the user said "broad", run all categories. If the user specified a focus area (e.g. "data science"), prioritize queries from that category.

**Use the installed CLI tools as the primary search mechanism.** Fall back to `WebSearch` only for portals that do not have a CLI skill, or if `bun` is unavailable on the system.

#### 1a. Check bun + python availability

```bash
bun --version
python3 --version
```

If `bun` is missing, skip bun-based CLIs. If `python3` is missing, skip Python CLIs. Fall back to **1d (WebSearch)** for any portal whose runtime is unavailable.

#### 1b. Discover + classify installed portal CLI skills

Discover all installed portal skills by reading every `SKILL.md` under `.agents/skills/*/SKILL.md`. Each documents its own CLI flags. Classify each into one of two tiers:

- **Tier A — API-fed CLIs** (JSON/RSS/API, fast & parallel): most portal CLIs. Invoke via `bun run .agents/skills/<name>/cli/src/cli.ts search …`.
- **Tier B — Browser-automation CLIs** (Playwright, anti-CAPCHA, slow & sequential): use when the portal blocks direct API calls. Invoke via `bun run .agents/skills/<name>/cli/src/cli.ts search …` (same shape — the CLI itself drives Chromium). **Limit Tier B to ONE invocation at a time** and increase the per-call timeout.

For each Tier A skill:
1. Read its `SKILL.md` for the correct invocation and flags.
2. Translate query terms from `search-queries.md` into that portal's flag format.
3. Scope to the last 14 days using the portal's recency flag.
4. Cap results to ~20 per call.
5. Use `--format json` where supported.

Run all Tier A portal CLIs in parallel using the Agent tool. Collect `results` arrays into a single pool. Tier B CLIs run sequentially after.

If a CLI exits non-zero, log the error and continue — do not abort the whole search.

#### 1c. Special handling — LinkedIn recruiter posts (`linkedin-recruiter-scraper`)

The `linkedin-recruiter-scraper` (Tier B) uses public search engines via Playwright to find
LinkedIn POST permalinks that include an apply-by-email address. When it's in scope:

1. Build `site:linkedin.com/posts` queries from `search-queries.md` terms (add `hiring`, `send your CV`, `apply at`, `email`).
2. Run ONE query at a time: `bun run .agents/skills/linkedin-recruiter-scraper/cli/src/cli.ts search --query "<query>" [--max-results N] [--engine google|bing]`
3. If `applyEmail` is non-null, it's a strong lead — flag it as **high-interest (email-apply possible)** in the results pool.
4. Each result feeds directly into the email application workflow (`linkedin_email_workflow.py`) — add these to the tracker with `channel: "linkedin"` and `status: "pending_user_action"` (or `interested`).

Deduplicate links against `seen_jobs.json`. Note: Tier B CLIs need Playwright Chromium (`bun install && npx playwright install chromium` once).

#### 1d. Messaging platforms — WhatsApp, Telegram, Discord

These sources fetch job offers shared in groups/channels. They need prior auth (one-time):

| Source | Auth | CLI command |
|--------|------|-------------|
| **Telegram** | `TELEGRAM_API_ID` + `TELEGRAM_API_HASH` env vars (https://my.telegram.org), then interactive phone verification | `bun run .agents/skills/telegram-search/cli/src/cli.ts fetch --group "GroupName" --limit 50` |
| **Discord** | `DISCORD_BOT_TOKEN` env var + bot invited to server | `bun run .agents/skills/discord-search/cli/src/cli.ts fetch --channel "jobs" --limit 50` |
| **WhatsApp** | QR scan (one-time, secondary number recommended) | `bun run .agents/skills/whatsapp-search/cli/src/cli.ts auth` then `listen` |

When in scope:
1. Read each messaging skill's `SKILL.md` for exact invocation.
2. Run fetch/listen per source. `applyEmail` + `channel: <source>` → strong lead.
3. OAuth-dependent: if auth not configured, **log a warning with setup instructions** and continue.
4. Deduplicate against `seen_jobs.json` + tracker.
5. Add results to tracker with `channel: "telegram"/"discord"/"whatsapp"`.

#### 1e. Image OCR — `jobs_images/` directory

The `image-ocr` skill extracts job data from images (screenshots, photos of offers).

1. If `jobs_images/` has images: `python3 .agents/skills/image-ocr/cli/ocr_cli.py batch --dir jobs_images/`
2. For single images: `python3 .agents/skills/image-ocr/cli/ocr_cli.py extract --image path.png`
3. Parsed results have `image_path` field for traceability.
4. Source tag: `source: "image_ocr"`.

Supported formats: PNG, JPG, JPEG, WEBP, BMP. Engine: rapidocr (primary) → pytesseract (fallback if Tesseract binary installed).

#### 1f. WebSearch fallback

Use `WebSearch` for:
- Portals listed in `search-queries.md` that do **not** have a corresponding directory under `.agents/skills/`
- Any portal whose CLI fails at runtime
- When bun is unavailable (Step 1a failed)

Use the site-specific query strings from `search-queries.md` directly as WebSearch queries for these portals.

### Step 2: Fetch & Parse

For each promising result from Step 1:

**From CLI results:** Search output already includes title, company, location, date,
and URL. For jobs worth a deeper look, fetch full detail with that portal's `detail`
command (see its SKILL.md — do not guess flags) to extract **key requirements**,
**application deadline**, and a brief description snippet.

**From WebSearch results:** Use `WebFetch` on the posting URL and extract the same
fields manually.

For every candidate:
- Skip if the URL or company+title combo already exists in `seen_jobs.json`
- Skip if the company+role already appears in `job_search_tracker.csv`

### Step 3: Quick Fit Assessment

For each new job, do a rapid fit check (NOT the full evaluation from `04-job-evaluation.md` - just a quick signal):

- **High match**: Role directly involves your core skills
- **Medium match**: Role is adjacent to your experience
- **Low match**: Role requires significant skills you lack

### Step 4: Deduplicate & Store

1. Add ALL fetched jobs (new and skipped) to `seen_jobs.json` with structure:
```json
{
  "seen": {
    "<url_or_company_title_key>": {
      "title": "...",
      "company": "...",
      "url": "...",
      "first_seen": "YYYY-MM-DD",
      "fit": "high/medium/low",
      "status": "new/skipped/evaluated/ranked/expired"
    }
  }
}
```

`/rank` extends this schema additively: ranked entries also carry `rank_score` (0–100 overall score), `rank_verdict` (fit band, e.g. "strong fit"), and `rank_date` (ISO date of ranking). The `status` field is set to `"ranked"`. Do not drop these fields when re-writing entries.

2. Only present jobs NOT already in the seen list or tracker.

### Step 5: Present Results

Present new jobs in a table sorted by fit (high first):

```
## New Job Matches - YYYY-MM-DD

Found X new positions (Y high, Z medium, W low match).

| # | Fit | Title | Company | Location | Deadline | URL |
|---|-----|-------|---------|----------|----------|-----|
| 1 | High | ... | ... | ... | ... | [Link](...) |

### High-Match Highlights
For each high-match job, add 2-3 bullet points:
- Why it matches your profile
- Key requirements to check
- Any red flags
```

After presenting, ask:
> "Want me to evaluate any of these in detail? Just give me the number(s)."

If the user picks a number, invoke the **job-application-assistant** skill workflow (fit evaluation first, then CV + cover letter if approved).

If the run found many new jobs (roughly 8+), also suggest `/rank` - it batch-scores all new postings against the full fit framework and returns a ranked shortlist, which beats eyeballing a long table. (`/rank` sets the `ranked` and `expired` status values in `seen_jobs.json`; treat both as already-seen for dedup purposes.)

### Step 6: Update Tracker (Optional)

If the user decides to apply to any job, add a row to `job_search_tracker.csv` using the standard header
defined in `outcome.md` Step 1 (17 columns). Populate `relocation_visa` (`sponsor`/`relocation`/`remote`/`none`/`unknown`)
and `salary_offered` from the posting when visible; set `status` to `interested` (or let `/apply` set `drafted`).

---

## Important Rules

1. **Never fabricate job postings.** Only present jobs from actual CLI search/detail output or WebSearch/WebFetch results.
2. **Respect deduplication.** Always check seen_jobs.json AND job_search_tracker.csv before presenting.
3. **Geography follows the mobility preference (CLAUDE.md → Mobility).** Do **not** skip jobs that require relocation — this candidate wants to relocate/migrate, so remote roles, on-site-abroad roles, and roles offering relocation/visa sponsorship are all in scope. Skip only jobs that are genuinely unreachable (on-site somewhere the candidate can't be, with no remote option and no relocation/visa support).
4. **Only open positions.** Skip postings with expired deadlines or those marked as closed.
5. **Be efficient with detail fetches.** Don't run `detail` or WebFetch on every search hit — pre-filter by title/snippet, then fetch only promising matches.
6. **Parallel searches.** Run portal CLI searches in parallel; use WebSearch only for gaps the CLIs don't cover.
