# Product Hunt Startup Search

Discover startups and their founders on Product Hunt.

## Trigger

Use this skill when the user wants to find startups on Product Hunt, especially newly launched products with accessible founders.

## How It Works

1. Queries Product Hunt GraphQL API for posts in tech categories
2. Extracts maker/founder names, profile links, and websites
3. Optionally finds founder emails via the email finder module

## Setup

Get a developer token from https://www.producthunt.com/v2/oauth/applications (doesn't expire).

Set in `.env`:
```
PRODUCT_HUNT_TOKEN=your_developer_token_here
```

## Commands

```bash
# Search for recently launched tech startups
bun run .agents/skills/producthunt-search/cli/src/cli.ts search --category "tech" --max-results 10

# Search for AI/developer tools startups
bun run .agents/skills/producthunt-search/cli/src/cli.ts search --category "ai" --max-results 10

# Search with specific tag
bun run .agents/skills/producthunt-search/cli/src/cli.ts search --tag "developer-tools" --max-results 10
```

## Output

```json
{
  "meta": { "count": 5 },
  "results": [
    {
      "id": "12345",
      "title": "Acme AI - AI-powered code review",
      "company": "Acme AI",
      "location": null,
      "date": "2026-08-01",
      "url": "https://www.producthunt.com/posts/acme-ai",
      "applyEmail": null,
      "emails": [],
      "author": "Jane Doe",
      "text": "Acme AI is an AI code review tool...",
      "source": "producthunt-launch"
    }
  ]
}
```

## Notes

- Product Hunt API is GraphQL-based, requires a developer token
- Free for non-commercial use
- Personal use only
