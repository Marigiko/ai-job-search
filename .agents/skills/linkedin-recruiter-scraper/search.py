#!/usr/bin/env python3
"""Playwright-backed search module for linkedin-recruiter-cli.

Finds LinkedIn recruiter post permalinks via public search engines. Called by the
bun CLI wrapper (`cli/src/commands/search.ts`) which parses args and formats output.
"""
import argparse
import re
import sys
import time
from urllib.parse import quote_plus, urlencode

from playwright.sync_api import sync_playwright

LINKEDIN_RE = re.compile(
    r"https?://(?:www\.)?linkedin\.com/(?:posts|feed/update/urn:li:activity:)[^\s\"'<>]+"
)


def search_urls(query: str, engine: str, max_results: int) -> list[str]:
    url = (
        f"https://www.google.com/search?{urlencode({'q': query, 'num': max_results * 3})}"
        if engine == "google"
        else f"https://www.bing.com/search?{urlencode({'q': query, 'count': max_results * 3})}"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        )
        page = ctx.new_page()
        try:
            with page.expect_navigation(wait_until="domcontentloaded", timeout=15000):
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        time.sleep(3)

        if "consent.google" in page.url or "sorry" in page.url:
            print("  [!] Google consent/CAPTCHA intercepted", file=sys.stderr)
            return []

        try:
            hrefs = page.evaluate(
                "() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)"
            )
        except Exception:
            hrefs = []

    raw = [u for u in hrefs if LINKEDIN_RE.match(u)]
    seen: set[str] = set()
    deduped: list[str] = []
    for u in raw:
        u = re.sub(r"[).,;]+$", "", u)
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped[:max_results]


def activity_id_from_url(url: str) -> str | None:
    m = re.search(r"(?:activity|ugcPost)[:-](\d{15,})", url) or re.search(r"(\d{18,})", url)
    return m.group(1) if m else None


def date_from_activity_id(id_: str | None) -> str | None:
    if not id_:
        return None
    try:
        ms = int(id_) >> 22
        if not ms or ms < 1_000_000_000_000 or ms > time.time() * 1000 + 86_400_000:
            return None
        from datetime import date

        return date.fromtimestamp(ms / 1000).isoformat()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--max-results", type=int, default=5)
    ap.add_argument("--engine", choices=["google", "bing"], default="bing")
    ap.add_argument("--format", choices=["json"], default="json")
    args = ap.parse_args()

    urls = search_urls(args.query, args.engine, args.max_results)
    results = []
    for u in urls:
        aid = activity_id_from_url(u)
        results.append(
            {
                "id": aid or u,
                "title": u,
                "company": None,
                "location": None,
                "date": date_from_activity_id(aid),
                "url": u.split("?")[0],
                "applyEmail": None,
                "emails": [],
                "author": None,
                "text": None,
                "source": "linkedin-recruiter-post",
            }
        )
    import json

    print(json.dumps({"results": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
