---
name: remotive-search
version: 1.0.0
description: >
  Use this skill to search live REMOTE job listings on Remotive, a remote-only job
  board with a public API and server-side keyword search. Every listing is remote.
  Useful for remote software, data, design, marketing and support roles, filterable
  by candidate location/timezone (e.g. Europe, USA, Worldwide). Invoke for remote
  job search, work-from-anywhere roles, or to look up a specific Remotive posting.
  Trigger phrases: remote jobs, remotive, work from anywhere, remote developer jobs,
  remote roles Europe/USA/LatAm timezone.
context: fork
allowed-tools: Bash(bun run .agents/skills/remotive-search/cli/src/cli.ts *)
---

# Remotive Search Skill

Search live remote job listings from [Remotive](https://remotive.com) via its public API.
No authentication, no API key, and **zero runtime dependencies** — runs with just `bun`.

**Every Remotive listing is remote.** Search is **server-side** (real keyword query); results carry
the candidate-required location/timezone (e.g. "Europe, UK", "USA Only", "Worldwide"), so `--location`
narrows to a region.

## Commands

### Search job listings

```bash
bun run .agents/skills/remotive-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keywords (server-side search). Recommended.
- `--location <text>` / `-l <text>` — filter by candidate-location substring (e.g. `USA`, `Europe`). Optional.
- `--visa` — only jobs whose text hints at visa sponsorship / relocation.
- `--jobage <days>` — only postings within N days.
- `--limit <n>` / `-n <n>` — cap results emitted. Default 50.
- `--format json|table|plain` — default `json`.

### Fetch full job detail

```bash
bun run .agents/skills/remotive-search/cli/src/cli.ts detail <id|url> [--format json|plain]
```

`id` is the numeric id from `search` results; a full job URL also works.

## Usage examples

```bash
bun run .agents/skills/remotive-search/cli/src/cli.ts search -q "backend developer" --format table
bun run .agents/skills/remotive-search/cli/src/cli.ts search -q python -l "Europe" --format table
bun run .agents/skills/remotive-search/cli/src/cli.ts detail 2091062 --format plain
```

## Output contract

Search emits `{ "meta": { "count", "page" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url` (missing values `null`), plus the Remotive extras
`remote` (always `true`), `visa`, `salaryText` (free-text or `null`), `jobType`, `category`, `tags`,
and `source: "remotive"`.

All errors go to **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.

## Notes

- Search is server-side; `--location`, `--visa`, and `--jobage` are applied client-side on top.
- Remotive salary is a free-text string (often empty) — exposed as `salaryText`, not parsed to a number.
- `detail` re-queries search (Remotive has no per-id endpoint); pass the `id` from a search result.
- `visa` is a best-effort text hint — always confirm in the posting.
