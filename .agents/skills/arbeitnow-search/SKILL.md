---
name: arbeitnow-search
version: 1.0.0
description: >
  Use this skill to search live job listings on Arbeitnow, a Germany/EU-focused,
  remote-friendly job board with a public JSON API. Especially useful for finding
  roles that mention visa sponsorship or relocation, and for remote positions
  payable in EUR/USD. Invoke for job search in Germany, the EU, or remote tech
  roles, or to look up a specific Arbeitnow posting. Trigger phrases: jobs in
  Germany, EU jobs, visa sponsorship jobs, relocation jobs, remote developer jobs,
  arbeitnow, find a job in Europe, "software jobs in Berlin/Munich".
context: fork
allowed-tools: Bash(bun run .agents/skills/arbeitnow-search/cli/src/cli.ts *)
---

# Arbeitnow Search Skill

Search live job listings from the [Arbeitnow](https://www.arbeitnow.com) public job-board API.
No authentication, no API key, and **zero runtime dependencies** — it runs with just `bun`.

Arbeitnow is Germany/EU-focused and remote-friendly, which makes it a strong fit for a
**relocation / visa-sponsorship** oriented search. The `--visa` flag surfaces postings whose
text hints at sponsorship or relocation support.

> Country-agnostic worked example of the repo's job-portal-skill pattern, backed by a JSON API
> (contrast with `linkedin-search`, which parses HTML). Public API — no ToS restriction on use.

## When to use this skill

- Search remote or EU/Germany-based openings by keyword
- Surface roles that mention visa sponsorship or relocation (`--visa`)
- Filter by recency or location substring
- Get the full description of a specific Arbeitnow posting

## Commands

### Search job listings

```bash
bun run .agents/skills/arbeitnow-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keywords (title/company/tags/description), AND semantics. Recommended.
- `--location <text>` / `-l <text>` — filter by location substring (client-side). Optional.
- `--remote` — only remote jobs.
- `--visa` — only jobs whose text hints at visa sponsorship / relocation.
- `--jobage <days>` — only postings within N days.
- `--page <n>` — 1-indexed start page (100 results/page upstream). Default 1.
- `--limit <n>` / `-n <n>` — cap total results emitted (client-side). Default 50.
- `--format json|table|plain` — default `json`.

### Fetch full job detail

```bash
bun run .agents/skills/arbeitnow-search/cli/src/cli.ts detail <slug|url> [--format json|plain]
```

`slug` is the `id` from `search` results (e.g. `backend-developer-remote-berlin-123`); a full
`arbeitnow.com/jobs/companies/.../<slug>` URL also works. Returns the full description text.

## Usage examples

```bash
# Remote backend roles
bun run .agents/skills/arbeitnow-search/cli/src/cli.ts search -q "backend developer" --remote --format table

# AI roles that mention visa sponsorship / relocation
bun run .agents/skills/arbeitnow-search/cli/src/cli.ts search -q "ai engineer" --visa --format table

# Python roles in Berlin, last 14 days
bun run .agents/skills/arbeitnow-search/cli/src/cli.ts search -q python -l Berlin --jobage 14

# Full detail for one posting
bun run .agents/skills/arbeitnow-search/cli/src/cli.ts detail backend-developer-remote-berlin-123 --format plain
```

## Output contract

Search emits `{ "meta": { "count", "page" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url` (missing values are `null`), plus the Arbeitnow extras
`remote` (bool), `visa` (`"sponsor"`/`"relocation"`/`null`), `tags`, `jobTypes`, and `source: "arbeitnow"`.

All errors are written to **stderr** as `{ "error": "...", "code": "..." }` and the process exits with code `1`.

## Notes

- The free API has **no server-side keyword search** — it returns the latest jobs (100/page). This CLI pages
  forward from `--page` (up to 5 pages) and filters client-side, so keyword/visa/location filters run locally.
- `visa` is a **best-effort text hint**, not an authoritative field — always confirm sponsorship in the posting.
- `detail` finds a slug by scanning recent pages; a posting that has aged out of the API window returns `NOT_FOUND`.
- Self-hosting: the data is Arbeitnow's public board; there is no key to configure.
