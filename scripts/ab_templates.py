#!/usr/bin/env python3
"""A/B testing for outreach email templates.

Manages multiple email templates, tracks usage, and reports which performs best.

Usage:
  python scripts/ab_templates.py list                  # Show all templates
  python scripts/ab_templates.py select                # Pick a template (round-robin or best)
  python scripts/ab_templates.py record <template_id> <company> <status>   # Record outcome
  python scripts/ab_templates.py stats                 # Show performance stats
  python scripts/ab_templates.py add                   # Add new template (interactive)
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from env_loader import load_env
load_env()

DATA_DIR = Path(__file__).parent.parent / "data"
TEMPLATES_FILE = DATA_DIR / "ab_templates.json"
OUTCOMES_FILE = DATA_DIR / "ab_outcomes.json"

DEFAULT_TEMPLATES = {
    "direct_value": {
        "name": "Direct Value",
        "subject": "{company} — founding engineer interest",
        "body": """Hi {founder_name},

I'm Mario, a full-stack dev from Argentina. I've been following {company} since {trigger}.

I specialize in building MVPs fast (shipped products in <72h at my last role) and AI automation (reduced ops friction significantly at a YC-backed startup).

I'm looking for a founding engineer role at a US startup like yours. I can start at $1K/mo to prove value — then we discuss equity.

Open to a 15-min call this week?

Best,
Mario Aquino
linkedin.com/in/keyzdev · github.com/Marigiko""",
    },
    "story_first": {
        "name": "Story First",
        "subject": "From Argentina to your founding team?",
        "body": """Hi {founder_name},

Quick story: I built my first MVP in 72 hours at a startup in Santa Fe. It got acquired 8 months later.

Since then I've been building AI automation systems at remote startups (Spain, Chile, El Salvador) — reducing deploy time by 50%, PR errors by 40%.

Now I'm looking to join a US startup as a founding engineer. I bring full-stack depth (Node, Python, AWS) + AI/LLM automation skills.

I can start at $1K/mo — low risk for you, and I prove value fast.

Worth a quick chat?

— Mario Aquino
linkedin.com/in/keyzdev""",
    },
    "question_hook": {
        "name": "Question Hook",
        "subject": "Quick question about {company}",
        "body": """Hi {founder_name},

I noticed {company} is building {trigger}. Quick question:

Are you planning to hire a founding engineer in the next 3-6 months?

I'm a full-stack dev (Node, Python, AWS, AI automation) from Argentina. I've shipped MVPs in <72h and built AI systems that cut ops friction in half.

I'm targeting US startups specifically — and I'm flexible on comp ($1K/mo to start, equity-focused).

If the timing is right, I'd love to share what I've been building.

Best,
Mario Aquino
linkedin.com/in/keyzdev · github.com/Marigiko""",
    },
    "social_proof": {
        "name": "Social Proof",
        "subject": "Built MVPs in 72h — interested in {company}",
        "body": """Hi {founder_name},

I'm Mario — I've been building products at remote startups for 5+ years.

Some highlights:
• Shipped an MVP in <72h at Syloper (Santa Fe)
• Reduced deploy time 50% at SalesMatch (Spain, YC-backed)
• Built AI automation that cut ops friction significantly
• Taught 150+ devs as a programming coach (92% satisfaction)

I'm now looking for a founding engineer role at a US startup. I can start at $1K/mo to prove value.

Open to a 15-min call?

— Mario Aquino
linkedin.com/in/keyzdev""",
    },
}


def load_templates() -> dict:
    if TEMPLATES_FILE.exists():
        with open(TEMPLATES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_templates(templates: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)


def load_outcomes() -> list:
    if OUTCOMES_FILE.exists():
        with open(OUTCOMES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_outcomes(outcomes: list):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTCOMES_FILE, "w", encoding="utf-8") as f:
        json.dump(outcomes, f, indent=2, ensure_ascii=False)


def ensure_templates_exist():
    """Initialize templates file if it doesn't exist."""
    if not TEMPLATES_FILE.exists():
        save_templates(DEFAULT_TEMPLATES)
        print(f"Initialized {len(DEFAULT_TEMPLATES)} default templates.")


def select_template(strategy: str = "best") -> tuple[str, dict]:
    """Select a template by strategy: 'best', 'random', 'round_robin'."""
    templates = load_templates()
    if not templates:
        ensure_templates_exist()
        templates = load_templates()

    outcomes = load_outcomes()

    if strategy == "random":
        tid = random.choice(list(templates.keys()))
        return tid, templates[tid]

    if strategy == "best":
        # Pick template with highest response rate (min 3 uses)
        stats = compute_stats(templates, outcomes)
        best_id = None
        best_rate = -1
        for tid, s in stats.items():
            if s["total"] >= 3 and s["response_rate"] > best_rate:
                best_rate = s["response_rate"]
                best_id = tid
        if best_id:
            return best_id, templates[best_id]
        # Not enough data — pick random
        tid = random.choice(list(templates.keys()))
        return tid, templates[tid]

    # round_robin: pick least recently used
    usage = {}
    for o in outcomes:
        tid = o.get("template_id")
        ts = o.get("timestamp", "")
        if tid not in usage or ts > usage[tid]:
            usage[tid] = ts
    for tid in templates:
        if tid not in usage:
            return tid, templates[tid]
    least_used = min(usage.keys(), key=lambda k: usage[k])
    return least_used, templates[least_used]


def compute_stats(templates: dict, outcomes: list) -> dict:
    stats = {}
    for tid in templates:
        t_outcomes = [o for o in outcomes if o.get("template_id") == tid]
        total = len(t_outcomes)
        responded = sum(1 for o in t_outcomes if o.get("status") in ("responded", "interview", "offer"))
        interviews = sum(1 for o in t_outcomes if o.get("status") in ("interview", "offer"))
        offers = sum(1 for o in t_outcomes if o.get("status") == "offer")
        stats[tid] = {
            "name": templates[tid].get("name", tid),
            "total": total,
            "responded": responded,
            "interviews": interviews,
            "offers": offers,
            "response_rate": round(responded / total * 100, 1) if total > 0 else 0,
            "interview_rate": round(interviews / total * 100, 1) if total > 0 else 0,
        }
    return stats


def cmd_list():
    ensure_templates_exist()
    templates = load_templates()
    outcomes = load_outcomes()
    stats = compute_stats(templates, outcomes)

    print(f"\n{'='*60}")
    print(f"EMAIL TEMPLATES ({len(templates)} total)")
    print(f"{'='*60}")
    for tid, tmpl in templates.items():
        s = stats.get(tid, {})
        uses = s.get("total", 0)
        rate = s.get("response_rate", 0)
        print(f"\n  [{tid}] {tmpl['name']} — {uses} uses, {rate}% response")
        print(f"    Subject: {tmpl['subject'][:60]}")
        print(f"    Preview: {tmpl['body'][:80]}...")


def cmd_select():
    ensure_templates_exist()
    tid, tmpl = select_template("best")
    print(f"\nSelected: [{tid}] {tmpl['name']}")
    print(f"Subject: {tmpl['subject']}")
    print(f"\n{tmpl['body']}")
    return tid, tmpl


def cmd_record(template_id: str, company: str, status: str):
    outcomes = load_outcomes()
    outcomes.append({
        "template_id": template_id,
        "company": company,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    save_outcomes(outcomes)
    print(f"Recorded: {status} for {company} (template: {template_id})")


def cmd_stats():
    ensure_templates_exist()
    templates = load_templates()
    outcomes = load_outcomes()
    stats = compute_stats(templates, outcomes)

    print(f"\n{'='*60}")
    print(f"TEMPLATE PERFORMANCE")
    print(f"{'='*60}")
    print(f"{'Template':<20} {'Uses':>5} {'Response':>10} {'Interview':>10} {'Offers':>8}")
    print(f"{'-'*53}")
    for tid, s in sorted(stats.items(), key=lambda x: x[1].get("response_rate", 0), reverse=True):
        print(f"{s['name']:<20} {s['total']:>5} {s['response_rate']:>9}% {s['interview_rate']:>9}% {s['offers']:>8}")
    print(f"\nTotal outcomes recorded: {len(outcomes)}")


def cmd_add():
    ensure_templates_exist()
    templates = load_templates()
    print("\nAdd new template:")
    tid = input("  Template ID (e.g., 'my_approach'): ").strip()
    if not tid or tid in templates:
        print("  Invalid or duplicate ID.")
        return
    name = input("  Display name: ").strip()
    subject = input("  Subject line ({company} and {founder_name} supported): ").strip()
    print("  Body (end with EOF on its own line):")
    lines = []
    while True:
        line = input()
        if line == "EOF":
            break
        lines.append(line)
    body = "\n".join(lines)
    templates[tid] = {"name": name, "subject": subject, "body": body}
    save_templates(templates)
    print(f"  Added template [{tid}] {name}")


def main():
    ap = argparse.ArgumentParser(description="A/B testing for email templates")
    sub = ap.add_subparsers(dest="command")

    sub.add_parser("list", help="List all templates")
    sub.add_parser("select", help="Select best template")

    record_p = sub.add_parser("record", help="Record outcome")
    record_p.add_argument("template_id")
    record_p.add_argument("company")
    record_p.add_argument("status", choices=["sent", "responded", "interview", "offer", "rejected", "no-response"])

    sub.add_parser("stats", help="Show performance stats")
    sub.add_parser("add", help="Add new template")

    args = ap.parse_args()

    if args.command == "list":
        cmd_list()
    elif args.command == "select":
        cmd_select()
    elif args.command == "record":
        cmd_record(args.template_id, args.company, args.status)
    elif args.command == "stats":
        cmd_stats()
    elif args.command == "add":
        cmd_add()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
