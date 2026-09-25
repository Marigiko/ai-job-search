# Search Queries for Job Scraper

<!-- SETUP: Customize these queries based on your skills, target roles, and location. -->
<!-- Target roles are the canonical list in CLAUDE.md → Target Roles. Keep the tiers below in sync. -->
<!-- GOAL: Enter the US startup market as a dev founder / founding engineer. Willing to accept $1000/mo for the right role. -->
<!-- CONTACT STRATEGY: All leads must be contactable by email for outbound automation. -->

## Installed portal CLIs (primary for `/scrape`)

`/scrape` discovers every portal skill under `.agents/skills/*/SKILL.md` and runs its CLI first. Shipped country-agnostic CLIs include `linkedin-search` and `freehire-search`; Danish demos and any skill you add with `/add-portal` are included the same way. You do **not** need a matching `site:` line below for those CLIs to run.

The `site:` query templates in this file are the **WebSearch fallback** — for portals without a CLI, company career pages, or when a CLI fails.

## Search Sites

Primary:
- **linkedin.com/jobs** — LinkedIn job listings (via `linkedin-search`; location passed explicitly, incl. "Remote")
- **linkedin.com/posts** — Recruiter hiring posts with apply-by-email (via `linkedin-posts-search` + `linkedin-recruiter-scraper`)
- **freehire.dev** — tech aggregator (via `freehire-search`; multi-market, remote facets)
- **The Muse** — US companies and startups (via `themuse-search`)
- **AngelList / Wellfound** — US startup jobs (email-contactable, equity-focused)

Secondary (company career pages via Google):
- Direct Google searches with `site:` filters for known US startup career pages
- Y Combinator job board (workatastartup.com)

## Query Categories

Queries are grouped by priority. The goal is **US startup / founding engineer roles paying $1000+ USD/mo or with equity**, all contactable by email.

### Priority 1: US Startup Founder / Founding Engineer Roles

```
site:linkedin.com/jobs "founding engineer" OR "first engineer" OR "technical co-founder" USA
site:linkedin.com/jobs "founding engineer" "pre-seed" OR "seed" "startup"
"founding engineer" "startup" "send your CV" OR "apply at" OR "email"
"technical co-founder" "startup" ("send CV" OR "apply" OR "contact") email
site:linkedin.com/posts "hiring" ("founding engineer" OR "first engineer" OR "technical co-founder") startup
site:linkedin.com/posts "send your CV" ("founding engineer" OR "first engineer") USA
"we're hiring" "founding engineer" OR "first engineer" startup email
"join our team" "technical co-founder" OR "founding engineer" email
```

### Priority 2: US Startup Developer Roles (Backend/AI/Full-Stack)

```
site:linkedin.com/jobs ("startup" OR "early-stage") ("backend developer" OR "AI engineer") USA remote
site:linkedin.com/jobs "software engineer" "startup" ("pre-seed" OR "seed" OR "Series A") USA
site:linkedin.com/posts "hiring" ("backend" OR "AI engineer" OR "full stack") "startup" email
"hiring" "software engineer" "startup" ("send your CV" OR "apply at") email
site:linkedin.com/jobs ("backend developer" OR "AI developer") "startup" "visa sponsorship" USA
"remote" "startup" "developer" ("apply" OR "send resume") email
```

### Priority 3: US Companies Hiring Remotely from LATAM

```
site:linkedin.com/jobs "remote" "USA" ("backend" OR "AI" OR "full stack") "contractor"
site:linkedin.com/jobs "remote" "US startup" ("node" OR "python" OR "AI") "contract"
"hiring remotely" "USA" "developer" email "apply"
site:linkedin.com/posts "remote developer" "USA" "startup" "send CV"
"remote" "hiring" "startup" "email" ("developer" OR "engineer")
```

### Priority 4: Email-Only Discovery (Recruiter Posts + Cold Outreach)

These queries target LinkedIn recruiter posts where the apply method is by email — the primary automation path.

```
site:linkedin.com/posts "hiring" ("backend" OR "AI" OR "full stack" OR "founding") ("send CV to" OR "email" OR "apply at")
site:linkedin.com/posts "we're hiring" ("startup" OR "early-stage") ("send your CV" OR "apply at")
site:linkedin.com/posts ("founding engineer" OR "first engineer") ("send your CV" OR "email")
site:linkedin.com/posts "hiring" ("node" OR "python" OR "AI") "startup" "email"
site:linkedin.com/posts "join our team" ("developer" OR "engineer") "startup" "send"
"send your CV to" ("startup" OR "founding" OR "first engineer") email
```

## Mobility Filter

Remote from Argentina to US companies is the primary mode. Relocation is a **goal, not a constraint**:
- **Remote (US company, USD pay ≥$1000/mo):** in scope — top priority
- **Remote with equity (startup):** in scope — preferred for founder roles
- **On-site US with relocation/visa:** in scope — but must justify the $1000/mo tradeoff
- **Local Argentina / non-US:** out of scope unless it's a US company's LATAM office

## Salary Filter

Only pursue postings whose stated pay meets the minimum band (CLAUDE.md → Compensation, currently 1000 USD/mo).
Where a portal supports a salary filter, set it to the minimum. If pay is not stated, keep the posting but flag
"salary undisclosed — confirm early". For founder roles with equity, lower cash compensation is acceptable if equity is meaningful.

## Contact Filter (NEW — email required)

**Every lead must have a contactable email.** Prioritize:
1. Postings that explicitly say "send your CV to <email>"
2. Recruiter posts with an apply-by-email
3. Company career pages with a direct email
4. LinkedIn jobs where the apply URL leads to an email-based application

Skip postings that ONLY have LinkedIn Easy Apply or an ATS with no email contact — these don't fit the automation workflow.

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline that has not yet passed. If a posting date cannot be determined, include it but flag as "date unknown".

## Discovery: LinkedIn recruiter posts (Primary Phase)

Many startup roles are advertised in recruiter *posts* with apply-by-email. This is the primary discovery path:
1. Use `linkedin-recruiter-scraper` to find recruiter posts for target roles/locations
2. Use `linkedin-posts-search extract <url>` to extract the apply email from each post
3. Feed emails into the `apply` skill for automated Gmail draft outreach

```
site:linkedin.com/posts ("send your CV" OR "apply at" OR "hiring") ("founding engineer" OR "first engineer" OR "backend" OR "AI") startup
site:linkedin.com/posts ("visa sponsorship" OR relocation) developer startup
```

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and also generate 2-3 custom queries for that focus. For example:
- "/scrape [focus_area]" -> relevant category queries + custom focus-specific queries
