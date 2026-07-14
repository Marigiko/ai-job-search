---
name: computrabajo-search
version: 1.0.0
description: >
  Use this skill to search live job listings on Computrabajo, the largest general
  job board across Latin America (Argentina by default, plus Mexico, Chile, Peru,
  Colombia, Uruguay, etc.). Best for local LatAm roles as a safety net alongside
  the remote/visa portals. Invoke for jobs in Argentina or Latin America, empleos
  en Argentina, trabajo en Buenos Aires, or to look up a specific Computrabajo
  offer. Trigger phrases: empleos Argentina, trabajo en Argentina, computrabajo,
  jobs in Latin America, trabajo Buenos Aires/CABA, empleo local.
context: fork
allowed-tools: Bash(bun run .agents/skills/computrabajo-search/cli/src/cli.ts *)
---

# Computrabajo Search Skill

Search live job listings from [Computrabajo](https://ar.computrabajo.com), the largest general job
board in Latin America. **Country-scoped** (defaults to **Argentina**), with `--country` for other
markets. No authentication, no API key, and **zero runtime dependencies** — runs with just `bun`.

This is the **LatAm/local safety net** portal (local on-site and hybrid roles) alongside the
remote/visa-oriented boards.

## ⚠️ Personal use only

This reads Computrabajo's public pages; automated access may be against their Terms of Service.
**Keep volume low and use it only for your own job search** — not commercially or for bulk
collection. Run it on your own responsibility.

## Commands

### Search job listings

```bash
bun run .agents/skills/computrabajo-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keywords (built into the Computrabajo search-URL slug). Recommended.
- `--country <code>` / `-c <code>` — country domain: `ar` (default), `mx`, `cl`, `pe`, `co`, `uy`, …
- `--location <text>` / `-l <text>` — filter by location substring (client-side, e.g. `"Buenos Aires"`).
- `--visa` — only jobs whose text hints at visa/relocation.
- `--page <n>` / `--limit <n>` / `-n <n>` — pagination / cap (default limit 50).
- `--format json|table|plain` — default `json`.

### Fetch full job detail

```bash
bun run .agents/skills/computrabajo-search/cli/src/cli.ts detail <offer-url|/path> [--country ar] [--format json|plain]
```

Pass the **`url`** from a search result (a bare hex id can't be resolved to a URL without its slug).

## Usage examples

```bash
# Developer roles in Argentina
bun run .agents/skills/computrabajo-search/cli/src/cli.ts search -q "desarrollador" -c ar --format table

# Backend roles filtered to Buenos Aires
bun run .agents/skills/computrabajo-search/cli/src/cli.ts search -q "backend developer" -c ar -l "Buenos Aires"

# Full detail for one offer
bun run .agents/skills/computrabajo-search/cli/src/cli.ts detail "https://ar.computrabajo.com/ofertas-de-trabajo/...-ABC123" --format plain
```

## Output contract

Search emits `{ "meta": { "count", "page", "country" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url` (missing values `null`), plus the extras `remote` (from the
posting's modality), `visa`, `posted` (raw relative text like "Hace 2 días"), and `source: "computrabajo"`.
`date` is an **approximate** ISO date derived from the relative `posted` text.

All errors go to **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.

## Notes

- HTML-scraped (like `linkedin-search`), so the parsing is more brittle than the JSON-API portals — if a field
  stops parsing, the site markup likely changed.
- `date` is approximate (derived from "Hace N días/horas"); the raw text is preserved in `posted`.
- `detail` fetches the offer page and extracts the "Descripción de la oferta" block; pass the offer `url`.
