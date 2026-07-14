---
name: jobicy-search
version: 1.0.0
description: >
  Use this skill to search live REMOTE job listings on Jobicy, a remote job board
  with a public API that supports region (geo) filtering — including USA, New
  Zealand, Europe, Canada, Australia — plus annual salary bands. Great for finding
  remote roles targeted at a specific country/region and for salary-aware search.
  Invoke for remote jobs in the USA / New Zealand / Europe, region-targeted remote
  roles, or to look up a specific Jobicy posting. Trigger phrases: remote jobs USA,
  remote jobs New Zealand, remote jobs Europe, jobicy, remote developer jobs by region.
context: fork
allowed-tools: Bash(bun run .agents/skills/jobicy-search/cli/src/cli.ts *)
---

# Jobicy Search Skill

Search live remote job listings from [Jobicy](https://jobicy.com) via its public API v2.
No authentication, no API key, and **zero runtime dependencies** — runs with just `bun`.

**Every Jobicy listing is remote**, but the `--geo` filter targets a **region** (`usa`,
`new-zealand`, `europe`, `canada`, `australia`, …), which makes this the go-to portal for
region-specific remote search (USA / NZ / Europe). Listings carry **annual salary bands**.

## Commands

### Search job listings

```bash
bun run .agents/skills/jobicy-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keyword (tag), server-side.
- `--geo <region>` / `-g <region>` — region slug: `usa`, `new-zealand`, `europe`, `canada`, `australia`, …
- `--visa` — only jobs whose text hints at visa sponsorship / relocation.
- `--min-salary <usd>` — only jobs whose rough monthly-USD estimate (annual ÷ 12) ≥ this floor.
- `--jobage <days>` — only postings within N days.
- `--limit <n>` / `-n <n>` — cap results (upstream max 50). Default 50.
- `--format json|table|plain` — default `json`.

### Fetch full job detail

```bash
bun run .agents/skills/jobicy-search/cli/src/cli.ts detail <id|url> [--format json|plain]
```

## Usage examples

```bash
# Remote developer roles targeted at the USA
bun run .agents/skills/jobicy-search/cli/src/cli.ts search -q developer -g usa --format table

# Remote roles targeted at New Zealand
bun run .agents/skills/jobicy-search/cli/src/cli.ts search -q engineer -g new-zealand --format table

# Remote roles targeted at Europe, paying ~3k USD/mo+
bun run .agents/skills/jobicy-search/cli/src/cli.ts search -q python -g europe --min-salary 3000

# Full detail for one posting
bun run .agents/skills/jobicy-search/cli/src/cli.ts detail 149243 --format plain
```

## Output contract

Search emits `{ "meta": { "count", "page" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url` (missing values `null`), plus the Jobicy extras
`remote` (always `true`), `visa`, `salaryMin`/`salaryMax`, `salaryCurrency`, `salaryPeriod`,
`level`, `tags` (industries), and `source: "jobicy"`.

All errors go to **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.

## Notes

- `location` is the target region (`jobGeo`), not a city — the role is remote.
- `--min-salary` compares a rough monthly estimate (annual ÷ 12); confirm exact figures in the posting.
- `visa` is a best-effort text hint — always confirm in the posting.
