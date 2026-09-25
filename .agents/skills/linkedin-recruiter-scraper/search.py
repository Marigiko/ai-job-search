#!/usr/bin/env python3
"""Search module for linkedin-recruiter-cli.

Finds LinkedIn recruiter post permalinks via public search engines.
Supports multiple backends:
  - serper: Serper.dev API (Google results, no CAPTCHA, 2500 free calls)
  - duckduckgo: DuckDuckGo HTML (free, no API key)
  - google/bing: Direct HTTP scraping (fallback)

Called by the bun CLI wrapper (`cli/src/commands/search.ts`).
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

LINKEDIN_RE = re.compile(
    r"https?://(?:www\.)?linkedin\.com/(?:posts|feed/update/urn:li:activity:)[^\s\"'<>]+"
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def search_serper(query: str, max_results: int) -> list[str]:
    """Search via Serper.dev API (Google results without CAPTCHA)."""
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return []
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": max_results * 3}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  [!] Serper error: {e}", file=sys.stderr)
        return []
    links = []
    for item in data.get("organic", []):
        href = item.get("link", "")
        if LINKEDIN_RE.match(href):
            links.append(href)
    return _dedup(links, max_results)


def search_duckduckgo(query: str, max_results: int) -> list[str]:
    """Search DuckDuckGo HTML (free, no API key needed)."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [!] DuckDuckGo error: {e}", file=sys.stderr)
        return []
    hrefs = re.findall(r'href="(https?://[^"]+)"', html)
    links = [u for u in hrefs if LINKEDIN_RE.match(u)]
    return _dedup(links, max_results)


def search_scrape(query: str, engine: str, max_results: int) -> list[str]:
    """Fallback: scrape Google/Bing directly (may hit CAPTCHA)."""
    encoded = urllib.parse.quote_plus(query)
    if engine == "google":
        url = f"https://www.google.com/search?num={max_results * 3}&q={encoded}"
    else:
        url = f"https://www.bing.com/search?count={max_results * 3}&q={encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [!] {engine} scrape error: {e}", file=sys.stderr)
        return []
    if "consent.google" in html.lower() or "sorry" in url:
        return []
    hrefs = re.findall(r'href="(https?://[^"]+)"', html)
    links = [u for u in hrefs if LINKEDIN_RE.match(u)]
    return _dedup(links, max_results)


def _dedup(urls: list[str], max_results: int) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for u in urls:
        u = re.sub(r"[).,;]+$", "", u)
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped[:max_results]


def search_urls(query: str, engine: str, max_results: int) -> list[str]:
    """Find LinkedIn post permalinks using the best available backend."""
    # Try Serper first (if API key set)
    results = search_serper(query, max_results)
    if results:
        return results
    # Try DuckDuckGo (free, no key)
    results = search_duckduckgo(query, max_results)
    if results:
        return results
    # Fallback: direct scrape
    return search_scrape(query, engine, max_results)


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
