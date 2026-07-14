---
name: linkedin-posts-search
version: 1.0.0
description: >
  Use this skill to turn a LinkedIn recruiter POST (not a jobs-section listing)
  into a structured lead with the apply-by-email address extracted. Many roles —
  especially in LatAm and startups — are advertised only in recruiter posts that
  say "send your CV to <email>". Give this skill a public LinkedIn post URL (or
  paste the post text) and it returns the author, post text, date, and the apply
  email. Invoke when the user shares a linkedin.com/posts/ URL, mentions applying
  by email from a LinkedIn post, or asks to extract a job/email from a recruiter
  post. Trigger phrases: linkedin post, recruiter post, apply by email, send CV to,
  extract email from post, linkedin.com/posts.
context: fork
allowed-tools: Bash(bun run .agents/skills/linkedin-posts-search/cli/src/cli.ts *)
---

# LinkedIn Posts Search Skill

Extract apply-by-email job leads from **public LinkedIn post permalinks** (or pasted post text).
No authentication, no API key, and **zero runtime dependencies** — runs with just `bun`.

Public LinkedIn post pages (`https://www.linkedin.com/posts/<slug>`) return HTTP 200 when logged out,
with Open Graph metadata (author/company + post text) and the body. This skill reads that, decodes the
post date from the activity id, and pulls the apply-by-email address (handling `[at]`/`[dot]`/`&#64;`
obfuscation). It is the bridge to the **email application workflow** (`/apply` with an `applyEmail`).

## ⚠️ Personal use only

Automated access to LinkedIn is against its Terms of Service. This skill only fetches **public post
permalinks you already have** (discovered via WebSearch, not by crawling the feed) or parses **text you
paste**. It does **not** search the LinkedIn feed. Keep volume low; run it on your own responsibility.

## Commands

### Extract from a public post URL

```bash
bun run .agents/skills/linkedin-posts-search/cli/src/cli.ts extract <post-url> [--format json|plain]
```

### Parse pasted post text (reliable fallback if a post is gated)

```bash
bun run .agents/skills/linkedin-posts-search/cli/src/cli.ts parse --text "<pasted post>" [--url <post-url>]
# or pipe it:
pbpaste | bun run .agents/skills/linkedin-posts-search/cli/src/cli.ts parse
```

### Discovery guidance

```bash
bun run .agents/skills/linkedin-posts-search/cli/src/cli.ts search -q "backend developer buenos aires"
```
Prints the compliant discovery workflow (it does not crawl the feed).

## Discovery workflow (how to find posts)

1. Use **WebSearch** for permalinks, e.g.
   `site:linkedin.com/posts ("send your CV" OR "apply at" OR hiring) <role> <location>`
   (these queries are also in `job-scraper/search-queries.md`).
2. Run `extract <url>` on each hit. If LinkedIn gates one, copy the post text and `parse --text`.
3. Feed the `applyEmail` + `text` into the email application workflow (`/apply`).

## Output contract

Emits `{ "meta": { "count": 1 }, "results": [ ... ] }` with at least `id, title, company, location,
date, url` (post `id` = activity id; `location` is `null`), plus the extras `applyEmail`, `emails`
(all found), `author`, `text`, and `source: "linkedin-post"`.

Errors go to **stderr** as `{ "error": "...", "code": "..." }`, exit code `1`.

## Authenticated mode (advanced — OFF by default)

Keyword search of the LinkedIn *feed* requires a logged-in session (the Voyager API) and is **against
LinkedIn's ToS**, so it is intentionally **not implemented**. If you understand the risk and set a
`LINKEDIN_COOKIE` environment variable, the `search` command still declines and points you to the
compliant WebSearch-then-extract workflow. Enabling real feed scraping would be your own responsibility
and is outside this repo's public-only pattern.

## Notes

- The post `date` is decoded from the activity id's high bits (no scraping needed).
- `applyEmail` is the first address found; `emails` lists all (in case there are several).
- If a post has no email, the lead still carries the text/author so you can apply via the normal channel.
