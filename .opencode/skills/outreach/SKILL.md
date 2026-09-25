# Outreach

Orchestrates the full outreach pipeline: discover → enrich → draft → send → track.

## Trigger

Use this skill when the user wants to run the full outreach campaign to US startups.

## Pipeline Phases

### Phase 1: Discovery
Run all installed portal scrapers to find startup job leads:
- `linkedin-recruiter-scraper search --query "founding engineer startup"` — LinkedIn recruiter posts
- `linkedin-recruiter-scraper search --query "technical co-founder email"` — more LinkedIn posts
- `yc-startup-search search --role "founding engineer" --remote` — YC startups
- `wellfound-search search --role "founding engineer" --remote` — Wellfound startups
- `bun run .agents/skills/producthunt-search/cli/src/cli.ts search --category "tech" --max-results 10` — Product Hunt launches
- `python scripts/scrape_emails.py` — multi-platform email scraper

Deduplicate results by company+role. Add new leads to `data/leads.csv` with status `new`.

### Phase 2: Enrichment
For each lead with status `new` and no email:
1. Extract company domain from URL or company name
2. Run `python scripts/email_finder.py --domain <domain> --role founder`
3. If email found, update lead with email + email_source, set status to `enriched`
4. If no email found, keep status as `new` for manual research

For leads that already have an email (from apply-by-email posts), set status to `enriched` directly.

### Phase 3: Scoring & Filtering
Filter enriched leads by fit:
- US startup (company location or domain indicates US)
- Role matches target (dev founder, founding engineer, first engineer, backend, AI)
- Not a duplicate of an already-contacted lead

### Phase 4: Drafting
For top enriched leads (max 5 per batch), generate personalized cold emails:
- Use the outreach email template
- Personalize with company name, founder name (if known), specific trigger
- Save drafts for user review

### Phase 5: Sending (Semi-Automatic)
Run `python scripts/outreach_sender.py --send` to:
1. Show preview of each email (uses A/B-tested templates by default)
2. Ask user approval (y/N/q) for each
3. Send approved emails with rate limiting (max 5/day)
4. Update lead status to `contacted` in `data/leads.csv`
5. Record template usage in `data/ab_outcomes.json` for A/B analysis

### Phase 6: Tracking
After sending, use `gmail-sync` to monitor responses:
- Interview invites → update status to `interview`
- Rejections → update status to `rejected`
- No response after 7 days → flag for follow-up

### Phase 7: Analytics
- Run `python scripts/dashboard.py --open` to view pipeline metrics
- Run `python scripts/ab_templates.py stats` to compare template performance
- Use data to refine templates and targeting

## Commands

```bash
# Full pipeline (dry run — preview only)
/outreach --dry-run

# Full pipeline (interactive — discover, enrich, draft, send with approval)
/outreach --send

# Discovery only
/outreach --discover

# Enrichment only (find emails for new leads)
/outreach --enrich

# Send only (send drafted emails from enriched leads)
/outreach --send --limit 3

# Analytics
python scripts/dashboard.py --open
python scripts/ab_templates.py stats
```

## Configuration

- `data/leads.csv` — Central leads database
- `data/ab_templates.json` — A/B tested email templates
- `data/ab_outcomes.json` — Template performance tracking
- `GMAIL_APP_PASSWORD` — Gmail app password (from .env)
- `HUNTER_API_KEY` — Hunter.io API key (optional, for email enrichment)
- `APOLLO_API_KEY` — Apollo.io API key (optional, for email enrichment)
- `SERPER_API_KEY` — Serper.dev API key (optional, for LinkedIn search)
- `PRODUCT_HUNT_TOKEN` — Product Hunt developer token (optional, for startup discovery)

## Output

All leads tracked in `data/leads.csv` with status lifecycle:
`new` → `enriched` → `drafted` → `contacted` → `responded` → `interview` → `offer` | `rejected` | `no-response`

## Notes

- **Anti-spam:** Never sends without manual approval. Max 5-10 emails/day with random delays.
- **A/B testing:** Templates are selected by best performance. Record outcomes to improve over time.
- **Personal use only:** All tools use public data only.
- **Dry run by default:** Always preview before sending.
