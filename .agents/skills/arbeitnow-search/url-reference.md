# Arbeitnow API reference

Data source: the public Arbeitnow job-board API. No authentication, no API key.

## Endpoint

```
GET https://www.arbeitnow.com/api/job-board-api?page=<n>
```

- Returns the latest jobs, **100 per page**, newest first.
- **No server-side keyword/location filter** in the free API — filtering is client-side in this CLI.
- Pagination via `?page=<n>` (1-indexed). Response includes `links.next` (null on the last page).

## Response shape

```json
{
  "data": [
    {
      "slug": "senior-software-engineer-remote-heidelberg-356036",
      "company_name": "GFN GmbH",
      "title": "Senior Software Engineer (Remote)",
      "description": "<p>HTML description…</p>",
      "remote": true,
      "url": "https://www.arbeitnow.com/jobs/companies/gfn-gmbh/senior-...-356036",
      "tags": ["Remote", "Software Development"],
      "job_types": ["full_time"],
      "location": "Heidelberg",
      "created_at": 1784032228
    }
  ],
  "links": { "first": "…", "last": null, "prev": null, "next": "…?page=2" },
  "meta": { "current_page": 1, "per_page": 100, "path": "…" }
}
```

## Field mapping (→ portal contract)

| API field | Result field | Notes |
|-----------|--------------|-------|
| `slug` | `id` | also the `detail` argument |
| `title` | `title` | |
| `company_name` | `company` | `null` if empty |
| `location` | `location` | `null` if empty |
| `created_at` | `date` | unix seconds → `YYYY-MM-DD` |
| `url` | `url` | canonical job page |
| `remote` | `remote` | boolean |
| — | `visa` | derived: `sponsor`/`relocation`/`null` from tags+title+description text |
| `tags` | `tags` | |
| `job_types` | `jobTypes` | |
| — | `source` | constant `"arbeitnow"` |

## Access

- `robots.txt`: the `/api/` endpoint is a documented public API intended for programmatic use.
- Auth: none required.
- ToS: public API; no personal-use restriction like LinkedIn. Keep request volume reasonable (backoff on 429/5xx is built in).
