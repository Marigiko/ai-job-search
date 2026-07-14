---
name: remoteok-search
version: 1.0.0
description: >
  Use this skill to search live REMOTE job listings on RemoteOK, a large
  remote-only job board with a public JSON API. Every listing is remote and many
  carry annual-USD salary bands, so it is ideal for finding remote roles that pay
  a target salary (e.g. a remote second income in USD). Invoke for remote job
  search, remote developer/design/marketing roles, work-from-anywhere positions,
  or to look up a specific RemoteOK posting. Trigger phrases: remote jobs, work
  from home, work from anywhere, remote developer jobs, remote OK, remote roles
  paying $X, digital nomad jobs.
context: fork
allowed-tools: Bash(bun run .agents/skills/remoteok-search/cli/src/cli.ts *)
---

# RemoteOK Search Skill

Search live remote job listings from the [RemoteOK](https://remoteok.com) public API.
No authentication, no API key, and **zero runtime dependencies** — runs with just `bun`.

**Every RemoteOK listing is remote**, and many include an **annual-USD salary band**
(`salaryMin`/`salaryMax`), which makes this the best portal for the "remote second income in
USD" goal — use `--min-salary` to keep only postings whose known pay clears your floor.

> Country-agnostic worked example of the repo's portal-skill pattern, backed by a JSON API.

## Attribution (RemoteOK API terms)

RemoteOK's API terms ask consumers to **link back to the job URL on Remote OK and credit Remote OK
as the source**. Keep the `url` field intact when presenting results. Public API, no login.

## When to use this skill

- Search remote openings by keyword
- Keep only jobs that clear a salary floor (`--min-salary <annual USD>`)
- Surface roles that hint at visa sponsorship / relocation (`--visa`)
- Get the full description of a specific RemoteOK posting

## Commands

### Search job listings

```bash
bun run .agents/skills/remoteok-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keywords (title/company/tags/description), AND semantics.
- `--location <text>` / `-l <text>` — filter by location substring (client-side). Optional.
- `--visa` — only jobs whose text hints at visa sponsorship / relocation.
- `--min-salary <usd>` — only jobs whose known annual-USD max is ≥ this floor (unknown-salary jobs are kept).
- `--jobage <days>` — only postings within N days.
- `--limit <n>` / `-n <n>` — cap results emitted (client-side). Default 50.
- `--format json|table|plain` — default `json`.

### Fetch full job detail

```bash
bun run .agents/skills/remoteok-search/cli/src/cli.ts detail <id|slug|url> [--format json|plain]
```

`id` is the numeric RemoteOK id from `search` results (e.g. `1134769`); a slug or full job URL also works.

## Usage examples

```bash
# Remote backend roles
bun run .agents/skills/remoteok-search/cli/src/cli.ts search -q "backend developer" --format table

# Remote python roles paying at least ~36k USD/yr (≈ 3k USD/mo)
bun run .agents/skills/remoteok-search/cli/src/cli.ts search -q python --min-salary 36000 --format table

# Roles hinting at visa sponsorship / relocation
bun run .agents/skills/remoteok-search/cli/src/cli.ts search -q "ai engineer" --visa

# Full detail for one posting
bun run .agents/skills/remoteok-search/cli/src/cli.ts detail 1134769 --format plain
```

## Output contract

Search emits `{ "meta": { "count", "page" }, "results": [...] }`. Each result has at least
`id, title, company, location, date, url` (missing values `null`), plus RemoteOK extras
`remote` (always `true`), `visa`, `salaryMin`/`salaryMax` (annual USD or `null`), `applyUrl`,
`tags`, and `source: "remoteok"`.

All errors are written to **stderr** as `{ "error": "...", "code": "..." }` and the process exits with code `1`.

## Notes

- The public API returns the latest ~100 jobs in one array whose **first element is a legal/metadata
  header** (skipped automatically). There is no server-side keyword search, so filters run client-side.
- Salaries are annual USD as reported by RemoteOK; `0`/absent → `null`. `--min-salary` never hides
  unknown-salary jobs (they are kept to confirm later), it only drops jobs with a known lower band.
- `visa` is a best-effort text hint — always confirm sponsorship in the posting.
