# Wellfound (AngelList) Startup Search

Discover jobs at startups listed on Wellfound (formerly AngelList).

## Trigger

Use this skill when the user wants to find jobs at startups on Wellfound/AngelList.

## How It Works

1. Searches DuckDuckGo/Bing for `site:wellfound.com` with role keywords
2. Extracts job listings with company name, role, and link
3. Optionally visits company pages to find founder contact info

## Commands

```bash
# Search for software engineer jobs at Wellfound startups
bun run .agents/skills/wellfound-search/cli/src/cli.ts search --role "software engineer" --max-results 10

# Search for founding engineer roles
bun run .agents/skills/wellfound-search/cli/src/cli.ts search --role "founding engineer" --remote --max-results 10

# Search by stage (pre-seed, seed, series-a)
bun run .agents/skills/wellfound-search/cli/src/cli.ts search --role "backend" --stage seed --max-results 10
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
      "url": "https://wellfound.com/...",
      "applyEmail": null,
      "emails": [],
      "author": null,
      "text": "...",
      "source": "wellfound-startup-job"
    }
  ]
}
```

## Notes

- Wellfound is JS-rendered, so we search via DuckDuckGo/Bing
- Results are public job listings, no authentication required
- Personal use only
