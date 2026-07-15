#!/usr/bin/env python3
"""
LinkedIn recruiter-post email application workflow.

Usage:
    python .agents/skills/job-scraper/linkedin_email_workflow.py --url <linkedin-post-url>
    python .agents/skills/job-scraper/linkedin_email_workflow.py --text "<post text>" --company "Acme" --role "Backend Dev"
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from linkedin_email_apply import get_apply_email, send_application_email

def extract_from_url(post_url: str) -> dict:
    """Use the linkedin-posts-search CLI to extract data from a public post URL."""
    result = subprocess.run(
        ["bun", "run",
         str(Path(__file__).parent.parent / "linkedin-posts-search" / "cli" / "src" / "cli.ts"),
         "extract", post_url, "--format", "json"],
        capture_output=True, text=True, cwd=str(Path(__file__).resolve().parent.parent.parent.parent)
    )
    if result.returncode != 0:
        return {"error": result.stderr}
    return json.loads(result.stdout)

def extract_from_text(text: str) -> dict:
    """Parse post text directly to extract applyEmail."""
    email = get_apply_email(text)
    return {
        "results": [{
            "applyEmail": email,
            "text": text,
        }]
    }

def main():
    parser = argparse.ArgumentParser(description="Apply to LinkedIn recruiter posts via email")
    parser.add_argument("--url", help="Public LinkedIn post URL")
    parser.add_argument("--text", help="Pasted post text")
    parser.add_argument("--company", help="Company name (used with --text)")
    parser.add_argument("--role", help="Role title (used with --text)")
    parser.add_argument("--cv", default="cv/main_example.pdf", help="Path to CV PDF")
    parser.add_argument("--cover", default=None, help="Path to cover letter PDF")
    parser.add_argument("--dry-run", action="store_true", help="Extract email but don't send")
    args = parser.parse_args()

    if args.url:
        data = extract_from_url(args.url)
    elif args.text:
        data = extract_from_text(args.text)
        if args.company:
            data["results"][0]["company"] = args.company
        if args.role:
            data["results"][0]["title"] = args.role
    else:
        print("ERROR: provide --url or --text")
        sys.exit(1)

    if "error" in data:
        print(f"ERROR: {data['error']}")
        sys.exit(1)

    results = data.get("results", [])
    if not results:
        print("No results extracted")
        sys.exit(1)

    for r in results:
        email = r.get("applyEmail")
        if not email:
            print(f"SKIP: no email found in post: {r.get('text', '')[:80]}...")
            continue

        title = r.get("title", args.role or "the position")
        print(f"Apply to: {email} for {title}")

        if args.dry_run:
            print(f"  DRY RUN - would send to {email}")
            continue

        try:
            send_application_email(email, args.cover, args.cv, title)
            print(f"  SENT to {email}")
        except Exception as e:
            print(f"  FAILED: {e}")

if __name__ == "__main__":
    main()
