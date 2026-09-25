#!/usr/bin/env python3
"""Generate an HTML dashboard from leads.csv metrics.

Usage:
  python scripts/dashboard.py
  python scripts/dashboard.py --open  # open in browser
"""
import argparse
import csv
import json
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from env_loader import load_env
load_env()

LEADS_CSV = Path(__file__).parent.parent / "data" / "leads.csv"
OUTPUT_HTML = Path(__file__).parent.parent / "data" / "dashboard.html"

CSV_FIELDS = [
    "id", "company", "role", "source", "url", "email", "email_source",
    "status", "date_found", "date_contacted", "response", "notes",
]


def load_leads() -> list[dict]:
    if not LEADS_CSV.exists():
        return []
    with open(LEADS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_metrics(leads: list[dict]) -> dict:
    total = len(leads)
    by_status = {}
    by_source = {}
    by_email_source = {}
    contacted = 0
    responded = 0
    interviews = 0
    offers = 0
    rejected = 0
    no_response = 0

    for lead in leads:
        status = lead.get("status", "unknown")
        source = lead.get("source", "unknown")
        email_source = lead.get("email_source", "none")

        by_status[status] = by_status.get(status, 0) + 1
        by_source[source] = by_source.get(source, 0) + 1
        if email_source and email_source != "none":
            by_email_source[email_source] = by_email_source.get(email_source, 0) + 1

        if status in ("contacted", "responded", "interview", "offer", "rejected", "no-response"):
            contacted += 1
        if status in ("responded", "interview", "offer"):
            responded += 1
        if status in ("interview", "offer"):
            interviews += 1
        if status == "offer":
            offers += 1
        if status == "rejected":
            rejected += 1
        if status == "no-response":
            no_response += 1

    response_rate = (responded / contacted * 100) if contacted > 0 else 0
    interview_rate = (interviews / contacted * 100) if contacted > 0 else 0

    return {
        "total": total,
        "by_status": by_status,
        "by_source": by_source,
        "by_email_source": by_email_source,
        "contacted": contacted,
        "responded": responded,
        "interviews": interviews,
        "offers": offers,
        "rejected": rejected,
        "no_response": no_response,
        "response_rate": round(response_rate, 1),
        "interview_rate": round(interview_rate, 1),
    }


def generate_html(metrics: dict, leads: list[dict]) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    status_json = json.dumps(metrics["by_status"], ensure_ascii=False)
    source_json = json.dumps(metrics["by_source"], ensure_ascii=False)

    # Recent leads table (last 20)
    recent = sorted(leads, key=lambda x: x.get("date_found", ""), reverse=True)[:20]
    rows_html = ""
    for lead in recent:
        status = lead.get("status", "")
        status_color = {
            "new": "#6b7280",
            "enriched": "#3b82f6",
            "drafted": "#8b5cf6",
            "contacted": "#f59e0b",
            "responded": "#10b981",
            "interview": "#059669",
            "offer": "#16a34a",
            "rejected": "#ef4444",
            "no-response": "#9ca3af",
        }.get(status, "#6b7280")
        rows_html += f"""<tr>
            <td>{lead.get('company', '')}</td>
            <td>{lead.get('role', '')}</td>
            <td><span class="badge" style="background:{status_color}">{status}</span></td>
            <td>{lead.get('source', '')}</td>
            <td>{lead.get('date_found', '')}</td>
            <td><a href="{lead.get('url', '#')}" target="_blank">link</a></td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Outreach Dashboard — Mario Aquino</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#0f172a; color:#e2e8f0; padding:24px; }}
h1 {{ font-size:24px; margin-bottom:4px; }}
.subtitle {{ color:#94a3b8; font-size:14px; margin-bottom:24px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:32px; }}
.card {{ background:#1e293b; border-radius:12px; padding:20px; border:1px solid #334155; }}
.card h3 {{ font-size:13px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px; }}
.card .value {{ font-size:32px; font-weight:700; }}
.card .sub {{ font-size:12px; color:#64748b; margin-top:4px; }}
.blue {{ color:#3b82f6; }} .green {{ color:#10b981; }} .yellow {{ color:#f59e0b; }}
.red {{ color:#ef4444; }} .purple {{ color:#8b5cf6; }} .gray {{ color:#94a3b8; }}
.charts {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:32px; }}
.chart-container {{ background:#1e293b; border-radius:12px; padding:20px; border:1px solid #334155; }}
.chart-container h3 {{ font-size:14px; margin-bottom:16px; }}
.bar {{ display:flex; align-items:center; margin-bottom:8px; }}
.bar-label {{ width:120px; font-size:12px; color:#94a3b8; text-transform:capitalize; }}
.bar-track {{ flex:1; background:#334155; border-radius:4px; height:20px; margin:0 8px; position:relative; }}
.bar-fill {{ height:100%; border-radius:4px; }}
.bar-value {{ font-size:12px; width:30px; }}
table {{ width:100%; border-collapse:collapse; background:#1e293b; border-radius:12px; overflow:hidden; border:1px solid #334155; }}
th {{ text-align:left; padding:12px 16px; font-size:12px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid #334155; }}
td {{ padding:10px 16px; font-size:13px; border-bottom:1px solid #1e293b; }}
tr:hover {{ background:#334155; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:12px; font-size:11px; color:#fff; }}
a {{ color:#3b82f6; text-decoration:none; }}
</style>
</head>
<body>
<h1>Outreach Dashboard</h1>
<p class="subtitle">Generated: {generated_at} | Target: US Startups — Dev Founder roles</p>

<div class="grid">
    <div class="card">
        <h3>Total Leads</h3>
        <div class="value blue">{metrics['total']}</div>
    </div>
    <div class="card">
        <h3>Contacted</h3>
        <div class="value yellow">{metrics['contacted']}</div>
    </div>
    <div class="card">
        <h3>Response Rate</h3>
        <div class="value green">{metrics['response_rate']}%</div>
        <div class="sub">{metrics['responded']} responses</div>
    </div>
    <div class="card">
        <h3>Interviews</h3>
        <div class="value purple">{metrics['interviews']}</div>
        <div class="sub">{metrics['interview_rate']}% of contacted</div>
    </div>
    <div class="card">
        <h3>Offers</h3>
        <div class="value green">{metrics['offers']}</div>
    </div>
    <div class="card">
        <h3>Rejected</h3>
        <div class="value red">{metrics['rejected']}</div>
        <div class="sub">{metrics['no_response']} no response</div>
    </div>
</div>

<div class="charts">
    <div class="chart-container">
        <h3>Leads by Status</h3>
        {generate_bars(metrics["by_status"], "#3b82f6")}
    </div>
    <div class="chart-container">
        <h3>Leads by Source</h3>
        {generate_bars(metrics["by_source"], "#8b5cf6")}
    </div>
</div>

<h3 style="margin-bottom:12px;">Recent Leads</h3>
<table>
<thead><tr><th>Company</th><th>Role</th><th>Status</th><th>Source</th><th>Date</th><th>Link</th></tr></thead>
<tbody>{rows_html if rows_html else '<tr><td colspan="6" style="text-align:center;color:#64748b;padding:24px">No leads yet</td></tr>'}</tbody>
</table>

</body>
</html>"""


def generate_bars(data: dict, color: str) -> str:
    if not data:
        return '<p style="color:#64748b;font-size:13px;">No data yet</p>'
    max_val = max(data.values()) if data else 1
    html = ""
    for label, val in sorted(data.items(), key=lambda x: x[1], reverse=True):
        pct = (val / max_val) * 100
        html += f"""<div class="bar">
            <span class="bar-label">{label}</span>
            <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div>
            <span class="bar-value">{val}</span>
        </div>"""
    return html


def main():
    ap = argparse.ArgumentParser(description="Generate outreach dashboard")
    ap.add_argument("--open", action="store_true", help="Open in browser after generating")
    args = ap.parse_args()

    leads = load_leads()
    metrics = compute_metrics(leads)
    html = generate_html(metrics, leads)

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard generated: {OUTPUT_HTML}")
    print(f"  Total leads: {metrics['total']}")
    print(f"  Contacted: {metrics['contacted']}")
    print(f"  Response rate: {metrics['response_rate']}%")
    print(f"  Interviews: {metrics['interviews']}")

    if args.open:
        webbrowser.open(f"file://{OUTPUT_HTML}")
        print("  Opened in browser.")


if __name__ == "__main__":
    main()
