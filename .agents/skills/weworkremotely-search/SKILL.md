---
name: weworkremotely-search
version: 1.0.0
description: >
  Use this skill to search live REMOTE job listings on We Work Remotely (WWR), a
  large remote-only job board, via its public RSS category feeds. Every listing is
  remote. Useful for remote developer, design, devops, product, and support roles
  payable from anywhere. Invoke for remote job search, work-from-anywhere roles, or
  to look up a specific WWR posting. Trigger phrases: remote jobs, work from home,
  work from anywhere, we work remotely, remote developer/design/devops jobs,
  remote-first roles.
context: fork
allowed-tools: Bash(bun run .agents/skills/weworkremotely-search/cli/src/cli.ts *)
---

# We Work Remotely Search Skill

Search live remote job listings from [We Work Remotely](https://weworkremotely.com) via its
public **RSS category feeds**. No authentication, no API key, and **zero runtime dependencies** —
runs with just `bun`.

**Every WWR listing is remote.** Search a category feed (programming, design, devops, …) and
filter client-side by keyword, region, or visa hint.

> Country-agnostic worked example of the repo's portal-skill pattern, backed by RSS/XML
> (contrast with the JSON-API portals `remoteok-search` and `arbeitnow-search`).

## When to use this skill

- Search remote openings in a WWR category by keyword
- Filter by region substring or visa/relocation hint
- Get the full description of a specific WWR posting

## Commands

### Search job listings

```bash
bun run .agents/skills/weworkremotely-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keywords (title/region/category/description), AND semantics.
- `--category <cat>` / `-c <cat>` — which feed. Default `programming`. One of:
  `programming, full-stack, back-end, front-end, devops, design, product, customer-support, sales, all`.
- `--location <text>` / `-l <text>` — filter by region substring (e.g. `"USA"`, `"Europe"`). Optional.
- `--visa` — only jobs whose text hints at visa sponsorship / relocation.
- `--limit <n>` / `-n <n>` — cap results emitted (client-side). Default 50.
- `--format json|table|plain` — default `json`.

### Fetch full job detail

```bash
bun run .agents/skills/weworkremotely-search/cli/src/cli.ts detail <slug|url> [--category <cat>] [--format json|plain]
```

`slug` is the `id` from `search` results; a full WWR job URL also works. Passing `--category`
makes the lookup faster (otherwise the common feeds are scanned).

## Usage examples

```bash
# Remote backend roles (programming feed)
bun run .agents/skills/weworkremotely-search/cli/src/cli.ts search -q "backend" --format table

# Remote React roles in the front-end feed
bun run .agents/skills/weworkremotely-search/cli/src/cli.ts search -q "react" -c front-end --format table

# Roles hinting at visa sponsorship / relocation
bun run .agents/skills/weworkremotely-search/cli/src/cli.ts search -q "engineer" --visa

# Full detail for one posting
bun run .agents/skills/weworkremotely-search/cli/src/cli.ts detail acme-senior-backend-developer --format plain
```

## Output contract

Search emits `{ "meta": { "count", "page", "category" }, "results": [...] }`. Each result has at
least `id, title, company, location, date, url` (missing values `null`), plus the WWR extras
`remote` (always `true`), `visa`, `category`, and `source: "weworkremotely"`. `company` is parsed
from the `"Company: Position"` RSS title, so it is `null` when the title has no company prefix.

All errors are written to **stderr** as `{ "error": "...", "code": "..." }` and the process exits with code `1`.

## Notes

- RSS feeds carry the latest jobs per category with no server-side keyword search — filtering runs client-side.
- The full description is embedded in the feed, so `detail` needs no extra page fetch.
- `visa` is a best-effort text hint — always confirm sponsorship in the posting.
