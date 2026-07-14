---
name: themuse-search
version: 1.0.0
description: >
  Use this skill to search live job listings on The Muse, a US-strong but global
  job board with a public API (no key). Its location filter targets specific
  cities/regions, so it is the primary portal for USA roles (US companies and
  cities) and also covers New Zealand, the UK/Europe, and remote ("Flexible /
  Remote"). Invoke for jobs in the USA, New Zealand, the UK/Europe, on-site or
  hybrid roles at named companies, or to look up a specific The Muse posting.
  Trigger phrases: jobs in the USA, jobs in New York/San Francisco, jobs in New
  Zealand/Auckland, jobs in London, the muse, on-site tech jobs, hybrid jobs.
context: fork
allowed-tools: Bash(bun run .agents/skills/themuse-search/cli/src/cli.ts *)
---

# The Muse Search Skill

Search live job listings from [The Muse](https://www.themuse.com) via its public API.
No authentication, no API key, and **zero runtime dependencies** — runs with just `bun`.

The Muse is **US-strong but global**: the `--location` filter targets a city/region string, so the
same skill covers **USA** (`"New York, NY"`, `"San Francisco, CA"`), **New Zealand**
(`"Auckland, New Zealand"`), the **UK/Europe** (`"London, United Kingdom"`, `"Berlin, Germany"`),
and remote (`"Flexible / Remote"`). Unlike the remote-only boards, it includes on-site and hybrid
roles at named companies.

## Commands

### Search job listings

```bash
bun run .agents/skills/themuse-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--location <text>` / `-l <text>` — city/region (server-side). e.g. `"New York, NY"`, `"Auckland, New Zealand"`.
- `--category <text>` / `-c <text>` — e.g. `"Software Engineering"`, `"Data Science"` (server-side).
- `--query <text>` / `-q <text>` — keywords (client-side; The Muse API has no keyword param).
- `--level <text>` — e.g. `"Entry Level"`, `"Mid Level"`, `"Senior Level"`.
- `--visa` — only jobs whose text hints at visa sponsorship / relocation.
- `--page <n>` / `--limit <n>` / `-n <n>` — pagination / cap (default limit 50).
- `--format json|table|plain` — default `json`.

### Fetch full job detail

```bash
bun run .agents/skills/themuse-search/cli/src/cli.ts detail <id> [--format json|plain]
```

`id` is the numeric job id from `search` results — fetched from The Muse's per-job endpoint.

## Usage examples

```bash
# Software Engineering roles in New York
bun run .agents/skills/themuse-search/cli/src/cli.ts search -c "Software Engineering" -l "New York, NY" --format table

# Backend roles in Auckland, New Zealand
bun run .agents/skills/themuse-search/cli/src/cli.ts search -q backend -l "Auckland, New Zealand" --format table

# Engineer roles in London
bun run .agents/skills/themuse-search/cli/src/cli.ts search -q engineer -l "London, United Kingdom"

# Full detail for one posting
bun run .agents/skills/themuse-search/cli/src/cli.ts detail 21610367 --format plain
```

## Output contract

Search emits `{ "meta": { "count", "page" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url` (missing values `null`), plus the extras `remote`
(true when the location is "Flexible / Remote"), `visa`, `level`, `category`, and `source: "themuse"`.

All errors go to **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.

## Notes

- The public API has **no keyword parameter** — `--query` filters client-side on title/company/category/contents.
- Best driven by `--location` (and `--category`), which are server-side; this is the repo's primary **USA** portal
  and a strong **New Zealand / UK / Europe** option.
- No salary data in the public API. `visa` is a best-effort text hint — always confirm in the posting.
