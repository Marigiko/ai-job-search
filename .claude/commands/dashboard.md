# /dashboard - Generate the Job Search Dashboard

You are generating a visual, offline HTML dashboard from the user's local job-search tracking data.

This command is a thin wrapper around `tools/dashboard.py`, which reads the tracking files and writes a
self-contained `dashboard.html` (no external dependencies, opens in any browser).

## Steps

1. Run the generator from the repo root:
   ```
   python3 tools/dashboard.py
   ```
   Optional flags:
   - `--min <N>` / `--ideal <N>` — override the salary band (defaults 2000 / 3000 USD/mo, matching CLAUDE.md → Compensation). If the user's band in CLAUDE.md differs, pass it here.
   - `--out <path>` — write somewhere other than `./dashboard.html`.

2. Report what it wrote (the script prints the application and scraped counts). Tell the user to open
   `dashboard.html` in their browser.

3. If the script reports **0 applications**, explain that the dashboard is empty because nothing has been
   tracked yet — point them to `/scrape` → `/apply` → `/outcome`, which populate the data the dashboard reads.

## What the dashboard shows
- Headline cards: total applications, active, reached-interview, offers, hired, scraped pipeline.
- An application funnel (interested → drafted → applied → interview → offer → hired).
- A filterable table (by status, role type, channel, relocation/visa) with a salary indicator vs the target band
  and a relocation/visa traffic-light dot.

## Notes
- Data sources: `job_search_tracker.csv`, `job_scraper/seen_jobs.json`, `documents/applications/**/outcome.md`.
- The salary indicator normalizes to a **monthly figure** with a simple heuristic (annual ÷ 12, `k` suffixes,
  hourly × 160). It does **not** convert currencies — a EUR/yr figure is compared as-is; treat colors as a guide.
- `dashboard.html` is gitignored — it is built from personal data and never committed.
