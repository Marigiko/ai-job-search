---
name: landingjobs-search
version: 1.0.0
description: >
  Use this skill to search live tech job listings on Landing.jobs, a European
  tech job board with a public API. Many roles are relocation- or visa-friendly
  (a `relocation_paid` flag), which makes it a strong fit for a migration-oriented
  search into the EU. Invoke for tech jobs in Europe, relocation/visa-sponsor
  roles, remote EU roles, or to look up a specific Landing.jobs posting. Trigger
  phrases: jobs in Europe, EU tech jobs, relocation jobs, visa sponsorship Europe,
  landing.jobs, remote developer jobs Europe, move to Portugal/Netherlands/Germany.
context: fork
allowed-tools: Bash(bun run .agents/skills/landingjobs-search/cli/src/cli.ts *)
---

# Landing.jobs Search Skill

Search live tech job listings from [Landing.jobs](https://landing.jobs) via its public API v1.
No authentication, no API key, and **zero runtime dependencies** — runs with just `bun`.

Landing.jobs is EU-focused and **relocation/visa friendly**: postings carry a `relocation_paid`
flag, surfaced here as `visa: "relocation"`. Combined with `--visa`, this is a good portal for the
migration goal. Salaries are annual gross in the posting's currency (mostly EUR).

> Country-agnostic worked example of the repo's portal-skill pattern, backed by a JSON API.

## When to use this skill

- Search EU tech roles by keyword (`--remote` for remote-only)
- Surface relocation/visa-friendly roles (`--visa`)
- Keep only jobs clearing an annual-gross salary floor (`--min-salary`)
- Get the full description of a specific Landing.jobs posting

## Commands

### Search job listings

```bash
bun run .agents/skills/landingjobs-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keywords (title/tags/requirements/description), AND semantics.
- `--location <text>` / `-l <text>` — filter by location substring (e.g. `Berlin`, `PT`). Optional.
- `--remote` — only remote jobs.
- `--visa` — only jobs flagged `relocation_paid` or hinting visa/relocation in text.
- `--min-salary <n>` — only jobs whose known annual-gross max ≥ this floor (posting's currency; unknown kept).
- `--jobage <days>` — only postings within N days.
- `--page <n>` / `--limit <n>` / `-n <n>` — pagination / cap (default limit 50).
- `--format json|table|plain` — default `json`.

### Fetch full job detail

```bash
bun run .agents/skills/landingjobs-search/cli/src/cli.ts detail <id|url> [--format json|plain]
```

`id` is the numeric id from `search` results (e.g. `19066`); a full job URL also works.

## Usage examples

```bash
# EU backend roles
bun run .agents/skills/landingjobs-search/cli/src/cli.ts search -q "backend developer" --format table

# Relocation/visa-friendly Java roles
bun run .agents/skills/landingjobs-search/cli/src/cli.ts search -q java --visa --format table

# Remote Python roles
bun run .agents/skills/landingjobs-search/cli/src/cli.ts search -q python --remote

# Full detail for one posting
bun run .agents/skills/landingjobs-search/cli/src/cli.ts detail 19066 --format plain
```

## Output contract

Search emits `{ "meta": { "count", "page" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url` (missing values `null`), plus the Landing.jobs extras
`remote`, `visa` (`"relocation"` when `relocation_paid`, else a text hint), `salaryLow`/`salaryHigh`
(annual gross or `null`), `currency`, `tags`, and `source: "landingjobs"`.

All errors are written to **stderr** as `{ "error": "...", "code": "..." }` and the process exits with code `1`.

## Notes

- The feed returns the latest jobs with no server-side keyword search — filtering runs client-side.
- **Company is not an API field**; it is derived from the job URL slug (`/at/<company>/…`), so it is a
  best-effort title-cased name.
- Salaries are annual gross in each posting's `currency` (mostly EUR) — `--min-salary` compares the raw number.
- `visa` is a best-effort signal (`relocation_paid` is authoritative for relocation; sponsorship is text-inferred) —
  always confirm in the posting.
