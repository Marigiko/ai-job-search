# Search Queries for Job Scraper

<!-- SETUP: Customize these queries based on your skills, target roles, and location. -->
<!-- Target roles are the canonical list in CLAUDE.md → Target Roles. Keep the tiers below in sync. -->
<!-- This candidate seeks a SECOND role, remote-in-USD or with relocation/visa (goal: migrate). -->

## Installed portal CLIs (primary for `/scrape`)

`/scrape` discovers every portal skill under `.agents/skills/*/SKILL.md` and runs its CLI first. Shipped country-agnostic CLIs include `linkedin-search` and `freehire-search`; Danish demos and any skill you add with `/add-portal` are included the same way. You do **not** need a matching `site:` line below for those CLIs to run.

The `site:` query templates in this file are the **WebSearch fallback** — for portals without a CLI, company career pages, or when a CLI fails.

## Search Sites

Primary:
- **linkedin.com/jobs** — LinkedIn job listings (via `linkedin-search`; location passed explicitly, incl. "Remote")
- **freehire.dev** — tech aggregator (via `freehire-search`; multi-market, remote facets)
- **Visa/relocation & remote boards** — added via `/add-portal` (Arbeitnow, RemoteOK, We Work Remotely, Relocate.me, Landing.jobs, VanHack)
- **Computrabajo (ar) + GetOnBoard** — LatAm/Argentina safety net (`computrabajo-search --country ar`, `getonbrd-search`)

Secondary (company career pages via Google):
- Direct Google searches with `site:` filters for known target companies

## Query Categories

Queries are grouped by priority. Because the goal is remote-USD or relocation/visa, prefer the modifiers
`remote`, `"visa sponsorship"`, and `relocation` on international queries. Local queries are a fallback.

### Priority 1: Backend Developer & AI Developer (strongest, most desired)

```
site:linkedin.com/jobs "backend developer" remote
site:linkedin.com/jobs "backend engineer" "visa sponsorship"
site:linkedin.com/jobs ("web scraping" OR "data pipeline" OR "python") remote
site:linkedin.com/jobs ("AI engineer" OR "AI developer" OR "LLM" OR "agents") remote
site:linkedin.com/jobs ("AI engineer" OR "RAG" OR "LLM") "relocation"
```

### Priority 2: Frontend Developer & VibeCoder / AI-assisted builder

```
site:linkedin.com/jobs "frontend developer" remote
site:linkedin.com/jobs "full stack developer" ("visa sponsorship" OR relocation)
site:linkedin.com/jobs ("AI-assisted" OR "prompt engineer" OR "vibe coding" OR "product engineer") remote
```

### Priority 3: Relocation / visa-sponsor focused (any of the above roles)

Target boards and phrasing that surface migration-friendly employers.

```
site:arbeitnow.com (backend OR "ai engineer" OR frontend) "visa sponsorship"
site:remoteok.com (backend OR python OR "ai engineer")
site:relocate.me developer
"software engineer" "visa sponsorship" (Netherlands OR Germany OR "New Zealand" OR Canada OR USA)
"backend developer" "relocation package"
```

### Priority 4: Broader net (contract / part-time second income)

```
site:linkedin.com/jobs (python OR "backend developer") ("part-time" OR contract) remote
site:freehire.dev backend remote
site:linkedin.com/jobs "developer" remote (contract OR freelance)
```

## Mobility Filter

Relocation is a **goal, not a constraint** (CLAUDE.md → Mobility). When evaluating results:
- **Fully remote (USD pay in the target band):** in scope — top priority for the "second income now" case.
- **On-site abroad with relocation/visa support:** in scope and preferred (aligns with migration goal).
- **On-site abroad without support, candidate willing to relocate:** in scope, FLAG the relocation cost.
- **Local on-site Resistencia (Chaco) / Argentina within commute, or Buenos Aires:** in scope as a fallback.
- **On-site somewhere unreachable with no remote/relocation path:** out of scope.

## Salary Filter

Only pursue postings whose stated pay meets the minimum band (CLAUDE.md → Compensation, currently 2000 USD/mo).
Where a portal supports a salary filter, set it to the minimum. If pay is not stated, keep the posting but flag
"salary undisclosed — confirm early".

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline that has not yet passed. If a posting date cannot be determined, include it but flag as "date unknown".

## Discovery: LinkedIn recruiter posts (Phase 3)

Many roles are advertised in recruiter *posts* (often with an apply-by-email), not the jobs section. Discover public
post permalinks via WebSearch, then hand the URL to `linkedin-posts-search extract <url>`:

```
site:linkedin.com/posts ("send your CV" OR "apply at" OR "hiring") ("backend" OR "ai engineer" OR frontend) remote
site:linkedin.com/posts ("visa sponsorship" OR relocation) developer
```

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and also generate 2-3 custom queries for that focus. For example:
- "/scrape [focus_area]" -> relevant category queries + custom focus-specific queries
