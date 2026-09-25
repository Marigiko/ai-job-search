# YC Startup Search

Discover jobs at Y Combinator startups via public search engines.

## Trigger

Use this skill when the user wants to find jobs at Y Combinator-backed startups.

## How It Works

1. Searches DuckDuckGo/Bing for `site:workatastartup.com` with role keywords
2. Extracts job listings with company name, role, and link
3. Optionally visits company pages to find founder contact info

## Commands

```bash
# Search for software engineer jobs at YC startups
bun run .agents/skills/yc-startup-search/cli/src/cli.ts search --role "software engineer" --max-results 10

# Search for founding engineer roles
bun run .agents/skills/yc-startup-search/cli/src/cli.ts search --role "founding engineer" --remote --max-results 10

# Search by batch (e.g., W26, S25)
bun run .agents/skills/yc-startup-search/cli/src/cli.ts search --role "backend" --batch W26 --max-results 10
```

## Output

```json
{
  "meta": { "count": 5 },
  "results": [
    {
      "id": "...",
      "title": "Founding Engineer at Acme AI",
      "company": "Acme AI",
      "location": "San Francisco, CA",
      "date": null,
      "url": "https://www.workatastartup.com/jobs/...",
      "applyEmail": null,
      "emails": [],
      "author": null,
      "text": "...",
      "source": "yc-startup-job"
    }
  ]
}
```

## Notes

- YC's workatastartup.com is JS-rendered, so we search via DuckDuckGo/Bing
- Results are public job listings, no authentication required
- Personal use only
