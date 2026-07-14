---
name: getonbrd-search
version: 1.0.0
description: >
  Use this skill to search live tech job listings on Get on Board (getonbrd.com),
  a major Latin America + remote tech job board with a public API and real
  server-side search. Salaries are reported in MONTHLY USD, which makes it ideal
  for matching a monthly target salary. Great for LatAm-based candidates and for
  remote roles across the Americas. Invoke for tech job search in Latin America,
  remote developer/data/design roles, jobs in Chile/Peru/Argentina/Mexico/Colombia,
  or to look up a specific Get on Board posting. Trigger phrases: getonbrd, get on
  board, trabajos remoto, empleos LatAm, remote jobs Latin America, developer jobs
  Peru/Chile/Mexico.
context: fork
allowed-tools: Bash(bun run .agents/skills/getonbrd-search/cli/src/cli.ts *)
---

# Get on Board Search Skill

Search live tech job listings from [Get on Board](https://www.getonbrd.com) via its public API v0.
No authentication, no API key, and **zero runtime dependencies** — runs with just `bun`.

Get on Board is a large **Latin America + remote** tech board. Two things make it valuable here:
its search is **server-side** (real keyword + remote + pagination), and its **salaries are monthly
USD** — directly comparable to a monthly target band. Use `--min-salary` to keep only postings whose
known monthly pay clears your floor.

> Country-agnostic worked example of the repo's portal-skill pattern, backed by a JSON:API-style API.

## When to use this skill

- Search LatAm / remote tech roles by keyword (`--remote` for remote-only)
- Keep only jobs that clear a monthly-USD salary floor (`--min-salary`)
- Surface roles hinting at visa sponsorship / relocation (`--visa`)
- Get the full description of a specific Get on Board posting

## Commands

### Search job listings

```bash
bun run .agents/skills/getonbrd-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keywords (server-side search). Recommended.
- `--remote` — only remote jobs.
- `--visa` — only jobs whose text hints at visa sponsorship / relocation.
- `--min-salary <usd>` — only jobs whose known **monthly**-USD max is ≥ this floor (unknown-salary jobs kept).
- `--jobage <days>` — only postings within N days.
- `--page <n>` / `--per-page <n>` — pagination (defaults 1 / 50).
- `--limit <n>` / `-n <n>` — cap results emitted. Default 50.
- `--format json|table|plain` — default `json`.

### Fetch full job detail

```bash
bun run .agents/skills/getonbrd-search/cli/src/cli.ts detail <slug|url> [--format json|plain]
```

`slug` is the `id` from `search` results; a full `getonbrd.com/jobs/<slug>` URL also works.

## Usage examples

```bash
# Remote backend roles
bun run .agents/skills/getonbrd-search/cli/src/cli.ts search -q "backend developer" --remote --format table

# Roles paying at least 2500 USD/month
bun run .agents/skills/getonbrd-search/cli/src/cli.ts search -q "python" --min-salary 2500 --format table

# Roles hinting at visa sponsorship / relocation
bun run .agents/skills/getonbrd-search/cli/src/cli.ts search -q "ai engineer" --visa

# Full detail for one posting
bun run .agents/skills/getonbrd-search/cli/src/cli.ts detail senior-backend-developer-acme-santiago-e811 --format plain
```

## Output contract

Search emits `{ "meta": { "count", "page" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url` (missing values `null`), plus the Get on Board extras
`remote`, `visa`, `salaryMin`/`salaryMax` (**monthly USD** or `null`), `seniority`, `category`, and
`source: "getonbrd"`.

All errors are written to **stderr** as `{ "error": "...", "code": "..." }` and the process exits with code `1`.

## Notes

- **JSON:API relationships:** `company` and `seniority` arrive as id references. The CLI resolves company
  names via `/companies/:id` (cached per run) and seniority via the `/seniorities` catalog (fetched once).
  If a lookup fails, that field is `null` rather than blocking the result.
- Salaries are **monthly USD** as reported by Get on Board; `0`/absent → `null`. `--min-salary` never hides
  unknown-salary jobs.
- The per-job API endpoint requires auth, so `detail` re-queries search with slug-derived keywords to fetch
  the full (public) description — pass the `id` straight from a `search` result for a reliable match.
- `visa` is a best-effort text hint — always confirm sponsorship in the posting.
