#!/usr/bin/env python3
"""Generate a self-contained HTML dashboard for the job search.

Reads the local (gitignored) tracking data and emits a single offline HTML file
with an application funnel, headline metrics, and a filterable table with salary
and relocation/visa indicators. Standard library only.

Usage:
    python3 tools/dashboard.py [--root DIR] [--out FILE] [--min 2000] [--ideal 3000]

Data sources (all optional; missing ones are handled gracefully):
    <root>/job_search_tracker.csv          - one row per application
    <root>/job_scraper/seen_jobs.json      - scraper funnel (scraped/ranked/expired)
    <root>/documents/applications/**/outcome.md - per-application status/notes

The output (dashboard.html) is gitignored - it is built from personal data.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

# --- Funnel definition -------------------------------------------------------

# Ordered active stages (progress) and terminal buckets.
ACTIVE_STAGES = ["interested", "drafted", "applied", "interview", "offer", "hired"]
TERMINAL_NEGATIVE = {"rejected", "no response", "offer declined", "withdrawn", "expired"}

# Feature (Phase 7): follow-up reminder — applications sitting in these stages
# longer than this many days without moving are flagged as "needs follow-up".
FOLLOWUP_DAYS = 10
FOLLOWUP_STAGES = {"applied", "interview"}


def days_since(date_str, today):
    """Whole days between an ISO date string and today (ISO). None if unparseable."""
    from datetime import date as _date
    try:
        d0 = _date.fromisoformat((date_str or "")[:10])
        d1 = _date.fromisoformat(today[:10])
        return (d1 - d0).days
    except (ValueError, TypeError):
        return None

# Normalize the various status spellings (CSV uses spaces, outcome.md uses
# underscores) to a single funnel stage.
STATUS_ALIASES = {
    "no_response": "no response",
    "offer_declined": "offer declined",
    "in_progress": "applied",  # outcome.md's catch-all -> at least applied
    "interview_only": "interview",
    "new": "interested",
    "ranked": "interested",
}


def normalize_status(raw: str) -> str:
    s = (raw or "").strip().lower()
    return STATUS_ALIASES.get(s, s)


# --- Salary parsing ----------------------------------------------------------

def parse_monthly_usd(raw: str):
    """Best-effort parse of a salary string into monthly USD. Returns float or None."""
    if not raw:
        return None
    text = raw.lower().replace(",", "").replace("$", " ").replace("usd", " ")
    # capture the first number, optionally with a 'k' suffix
    m = re.search(r"(\d+(?:\.\d+)?)\s*(k?)", text)
    if not m:
        return None
    value = float(m.group(1))
    if m.group(2) == "k":
        value *= 1000
    # infer period
    if re.search(r"/?\s*(yr|year|annum|anual|annual|/a\b)", text) or value >= 20000:
        # annual figure -> monthly (20k+ almost certainly annual for these markets)
        value /= 12
    elif re.search(r"/?\s*(hr|hour|hora)", text):
        value *= 160  # ~full-time month
    # weekly / daily left as-is (rare); good enough for a heuristic dashboard
    return round(value)


def salary_class(monthly, minimum, ideal):
    if monthly is None:
        return "unknown"
    if monthly < minimum:
        return "below"
    if monthly >= ideal:
        return "ideal"
    return "ok"


def visa_class(raw: str) -> str:
    s = (raw or "").strip().lower()
    if s in ("sponsor", "sponsorship", "relocation", "reloc"):
        return "green"
    if s == "remote":
        return "blue"
    if s in ("none", "no"):
        return "grey"
    return "amber"  # unknown / blank


# --- Data loading ------------------------------------------------------------

def load_tracker(root: Path):
    path = root / "job_search_tracker.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_seen(root: Path):
    path = root / "job_scraper" / "seen_jobs.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    seen = data.get("seen", {}) if isinstance(data, dict) else {}
    return seen if isinstance(seen, dict) else {}


def load_outcomes(root: Path):
    """Return {folder_name: status} parsed from outcome.md Status lines."""
    base = root / "documents" / "applications"
    result = {}
    if not base.exists():
        return result
    for md in base.glob("*/outcome.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\*\*Status:\*\*\s*([A-Za-z_ ]+)", text)
        if m:
            # take the first token option (before any '|' list of placeholders)
            status = m.group(1).split("|")[0].strip()
            result[md.parent.name] = normalize_status(status)
    return result


# --- HTML rendering ----------------------------------------------------------

CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  margin: 0; padding: 24px; background: #f6f7f9; color: #1a1a1a; }
h1 { font-size: 22px; margin: 0 0 4px; }
.sub { color: #666; font-size: 13px; margin-bottom: 20px; }
.cards { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 22px; }
.card { background: #fff; border: 1px solid #e3e5e8; border-radius: 10px;
  padding: 14px 18px; min-width: 120px; }
.card .n { font-size: 26px; font-weight: 700; }
.card .l { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: .04em; }
.section { background: #fff; border: 1px solid #e3e5e8; border-radius: 10px;
  padding: 18px; margin-bottom: 22px; }
.section h2 { font-size: 15px; margin: 0 0 14px; }
.funnel { display: flex; flex-direction: column; gap: 6px; }
.frow { display: flex; align-items: center; gap: 10px; }
.frow .name { width: 110px; font-size: 13px; text-transform: capitalize; }
.frow .bar { height: 22px; border-radius: 5px; background: #4f7cff; min-width: 2px; }
.frow .cnt { font-size: 13px; color: #333; font-weight: 600; }
.controls { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; }
.controls input, .controls select { padding: 7px 9px; border: 1px solid #ccced2;
  border-radius: 7px; font-size: 13px; background: #fff; color: inherit; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #eceef0; vertical-align: top; }
th { font-size: 11px; text-transform: uppercase; letter-spacing: .03em; color: #777; cursor: default; }
tbody tr:hover { background: #f9fafb; }
.pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.st-interested{background:#eef;color:#4453b8}.st-drafted{background:#e7f0ff;color:#2f5fd0}
.st-applied{background:#e3f3e8;color:#1f8a4c}.st-interview{background:#fff3d6;color:#9a6b00}
.st-offer{background:#e6f7ef;color:#0a7d47}.st-hired{background:#d6f5e3;color:#066b3a}
.st-rejected,.st-expired{background:#f1f2f4;color:#888}
.dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; }
.green{background:#22a862}.blue{background:#3b82f6}.amber{background:#e5a300}.grey{background:#bbb}
.below{color:#c0392b;font-weight:700}.ok{color:#9a6b00}.ideal{color:#0a7d47;font-weight:700}.unknown{color:#999}
a { color: #2f5fd0; text-decoration: none; } a:hover { text-decoration: underline; }
.empty { color:#888; font-style: italic; }
.followup { cursor: help; }
.conv { display: flex; flex-wrap: wrap; gap: 24px; }
.conv > div { flex: 1; min-width: 280px; }
.conv h3 { font-size: 13px; margin: 0 0 8px; color: #555; }
table.mini td, table.mini th { padding: 5px 8px; }
@media (prefers-color-scheme: dark) {
  body{background:#15171b;color:#e6e7ea}.card,.section{background:#1e2127;border-color:#2c3038}
  .sub,.card .l,th{color:#9aa0aa}.controls input,.controls select{background:#1e2127;border-color:#3a3f48}
  tbody tr:hover{background:#22262d}th,td{border-color:#2c3038}.frow .cnt,.frow .name{color:#cfd3da}
}
"""


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def render(rows, seen, outcomes, minimum, ideal, today) -> str:
    # --- funnel from tracker ---
    stage_counts = Counter()
    for r in rows:
        st = normalize_status(r.get("status", ""))
        stage_counts[st] += 1

    # scraper funnel
    seen_counts = Counter(normalize_status(v.get("status", "")) if isinstance(v, dict) else ""
                          for v in seen.values())
    scraped_total = len(seen)

    # headline metrics
    total_apps = len(rows)
    active = sum(stage_counts[s] for s in ("interested", "drafted", "applied", "interview", "offer"))
    interviews = stage_counts["interview"] + stage_counts["offer"] + stage_counts["hired"]
    offers = stage_counts["offer"] + stage_counts["hired"]
    hired = stage_counts["hired"]

    # follow-up: rows stuck in applied/interview past FOLLOWUP_DAYS
    stale_ids = set()
    for i, r in enumerate(rows):
        st = normalize_status(r.get("status", ""))
        if st in FOLLOWUP_STAGES:
            ds = days_since(r.get("date", ""), today)
            if ds is not None and ds >= FOLLOWUP_DAYS:
                stale_ids.add(i)

    cards = [
        ("Applications", total_apps), ("Active", active),
        ("Reached interview", interviews), ("Offers", offers), ("Hired", hired),
        ("Needs follow-up", len(stale_ids)), ("Scraped (pipeline)", scraped_total),
    ]
    cards_html = "".join(
        f'<div class="card"><div class="n">{n}</div><div class="l">{esc(l)}</div></div>'
        for l, n in cards
    )

    # funnel bars (active stages)
    max_stage = max([stage_counts[s] for s in ACTIVE_STAGES] + [1])
    funnel_rows = ""
    for s in ACTIVE_STAGES:
        c = stage_counts[s]
        width = int(6 + (c / max_stage) * 94) if c else 2
        funnel_rows += (
            f'<div class="frow"><span class="name">{esc(s)}</span>'
            f'<span class="bar" style="width:{width}%"></span>'
            f'<span class="cnt">{c}</span></div>'
        )
    # negative outcomes summary line
    neg = {s: stage_counts[s] for s in TERMINAL_NEGATIVE if stage_counts[s]}
    neg_html = " · ".join(f"{esc(k)}: {v}" for k, v in neg.items()) or "none yet"

    scraper_line = (
        f'scraped: {scraped_total} · ranked: {seen_counts.get("interested", 0)} '
        f'· expired: {seen_counts.get("expired", 0)}'
    )

    # conversion analytics (Phase 7): by channel and by role type
    REACHED = {"interview", "offer", "hired"}

    def conversion(field):
        groups = {}
        for r in rows:
            key = (r.get(field) or "—").strip() or "—"
            g = groups.setdefault(key, {"total": 0, "reached": 0, "offers": 0})
            g["total"] += 1
            st = normalize_status(r.get("status", ""))
            if st in REACHED:
                g["reached"] += 1
            if st in ("offer", "hired"):
                g["offers"] += 1
        rowsy = ""
        for key, g in sorted(groups.items(), key=lambda kv: -kv[1]["total"]):
            rate = f'{round(100 * g["reached"] / g["total"])}%' if g["total"] else "—"
            rowsy += (
                f"<tr><td>{esc(key)}</td><td>{g['total']}</td>"
                f"<td>{g['reached']}</td><td>{g['offers']}</td><td>{rate}</td></tr>"
            )
        return rowsy or '<tr><td colspan="5" class="empty">no data yet</td></tr>'

    conv_channel = conversion("channel")
    conv_role = conversion("role_type")

    # --- table ---
    headers = ["Date", "Company", "Role", "Type", "Channel", "Status",
               "Salary (offered)", "Reloc/Visa", "Fit", "Link"]
    body = ""
    for i, r in enumerate(rows):
        st = normalize_status(r.get("status", ""))
        st_class = "st-" + re.sub(r"[^a-z]", "", st) if st else ""
        followup = ' <span title="needs follow-up" class="followup">⏰</span>' if i in stale_ids else ""
        offered = r.get("salary_offered", "")
        monthly = parse_monthly_usd(offered)
        scls = salary_class(monthly, minimum, ideal)
        sal_disp = esc(offered) if offered else '<span class="unknown">—</span>'
        if monthly is not None:
            sal_disp = f'<span class="{scls}">{esc(offered)} (~{monthly}/mo)</span>'
        vcls = visa_class(r.get("relocation_visa", ""))
        vlabel = r.get("relocation_visa", "") or "unknown"
        link = r.get("application_url") or r.get("source") or ""
        link_html = f'<a href="{esc(link)}" target="_blank">open</a>' if link else ""
        row_terms = " ".join(esc(r.get(k, "")) for k in
                             ("company", "role", "role_type", "channel")).lower()
        body += (
            f'<tr data-status="{esc(st)}" data-type="{esc(r.get("role_type",""))}" '
            f'data-channel="{esc(r.get("channel",""))}" data-visa="{esc(vlabel)}" '
            f'data-terms="{esc(row_terms)}">'
            f'<td>{esc(r.get("date",""))}</td>'
            f'<td>{esc(r.get("company",""))}</td>'
            f'<td>{esc(r.get("role",""))}</td>'
            f'<td>{esc(r.get("role_type",""))}</td>'
            f'<td>{esc(r.get("channel",""))}</td>'
            f'<td><span class="pill {st_class}">{esc(st)}</span>{followup}</td>'
            f'<td>{sal_disp}</td>'
            f'<td><span class="dot {vcls}"></span>{esc(vlabel)}</td>'
            f'<td>{esc(r.get("fit_rating",""))}</td>'
            f'<td>{link_html}</td></tr>'
        )
    if not body:
        body = ('<tr><td colspan="10" class="empty">No applications tracked yet. '
                'Run /apply on a job and it will appear here.</td></tr>')
    head_html = "".join(f"<th>{esc(h)}</th>" for h in headers)

    # filter option sets
    def opts(field):
        vals = sorted({(r.get(field) or "").strip() for r in rows if (r.get(field) or "").strip()})
        return "".join(f'<option value="{esc(v)}">{esc(v)}</option>' for v in vals)

    status_opts = "".join(
        f'<option value="{esc(s)}">{esc(s)}</option>'
        for s in sorted({normalize_status(r.get("status", "")) for r in rows if r.get("status")})
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job Search Dashboard</title><style>{CSS}</style></head><body>
<h1>Job Search Dashboard</h1>
<div class="sub">Generated {esc(today)} · target band: {minimum}–{ideal} USD/mo ·
data from job_search_tracker.csv, seen_jobs.json, outcome.md</div>

<div class="cards">{cards_html}</div>

<div class="section"><h2>Application funnel</h2>
<div class="funnel">{funnel_rows}</div>
<div class="sub" style="margin-top:12px">Closed: {neg_html}<br>Scraper pipeline — {scraper_line}</div>
</div>

<div class="section"><h2>Conversion</h2>
<div class="conv">
  <div><h3>By channel</h3><table class="mini"><thead><tr><th>Channel</th><th>Apps</th><th>Interview+</th><th>Offers</th><th>Rate</th></tr></thead><tbody>{conv_channel}</tbody></table></div>
  <div><h3>By role type</h3><table class="mini"><thead><tr><th>Role type</th><th>Apps</th><th>Interview+</th><th>Offers</th><th>Rate</th></tr></thead><tbody>{conv_role}</tbody></table></div>
</div>
<div class="sub" style="margin-top:10px">Rate = share of applications that reached at least an interview. Use it to double down on the channels/roles that convert.</div>
</div>

<div class="section"><h2>Applications</h2>
<div class="controls">
  <input id="q" type="text" placeholder="Search company / role…" oninput="flt()">
  <select id="fstatus" onchange="flt()"><option value="">All statuses</option>{status_opts}</select>
  <select id="ftype" onchange="flt()"><option value="">All role types</option>{opts('role_type')}</select>
  <select id="fchannel" onchange="flt()"><option value="">All channels</option>{opts('channel')}</select>
  <select id="fvisa" onchange="flt()"><option value="">All reloc/visa</option>
    <option value="sponsor">sponsor</option><option value="relocation">relocation</option>
    <option value="remote">remote</option><option value="none">none</option><option value="unknown">unknown</option>
  </select>
</div>
<table><thead><tr>{head_html}</tr></thead><tbody id="tb">{body}</tbody></table>
</div>

<script>
function flt() {{
  var q=document.getElementById('q').value.toLowerCase();
  var st=document.getElementById('fstatus').value;
  var ty=document.getElementById('ftype').value;
  var ch=document.getElementById('fchannel').value;
  var vi=document.getElementById('fvisa').value;
  document.querySelectorAll('#tb tr').forEach(function(tr){{
    if(!tr.dataset.terms){{tr.style.display='';return;}}
    var ok = (!q||tr.dataset.terms.indexOf(q)>-1)
      && (!st||tr.dataset.status===st) && (!ty||tr.dataset.type===ty)
      && (!ch||tr.dataset.channel===ch) && (!vi||(tr.dataset.visa||'').toLowerCase()===vi);
    tr.style.display = ok ? '' : 'none';
  }});
}}
</script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Generate the job search dashboard HTML.")
    default_root = Path(__file__).resolve().parent.parent
    ap.add_argument("--root", type=Path, default=default_root, help="repo root (data location)")
    ap.add_argument("--out", type=Path, default=None, help="output HTML path")
    ap.add_argument("--min", type=int, default=2000, help="minimum acceptable monthly USD")
    ap.add_argument("--ideal", type=int, default=3000, help="ideal monthly USD")
    args = ap.parse_args()

    root = args.root
    out = args.out or (root / "dashboard.html")

    rows = load_tracker(root)
    seen = load_seen(root)
    outcomes = load_outcomes(root)

    # enrich tracker status from outcome.md where the CSV is behind
    for r in rows:
        company = (r.get("company") or "").strip().lower().replace(" ", "_")
        role = (r.get("role") or "").strip().lower().replace(" ", "_")
        key = f"{company}_{role}"
        if key in outcomes and normalize_status(r.get("status", "")) in ("applied", "in_progress", ""):
            r["status"] = outcomes[key]

    today = date.today().isoformat()
    out.write_text(render(rows, seen, outcomes, args.min, args.ideal, today), encoding="utf-8")
    print(f"dashboard: wrote {out} ({len(rows)} applications, {len(seen)} scraped)")


if __name__ == "__main__":
    main()
