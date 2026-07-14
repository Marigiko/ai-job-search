# Remotive API reference

Data source: the public Remotive API. No authentication, no API key.

## Endpoint

```
GET https://remotive.com/api/remote-jobs?search=<kw>&limit=<n>[&category=<slug>]
```

- **Server-side** keyword search via `search`. `limit` caps results.
- Response has meta keys (`0-legal-notice`, `job-count`, …) plus `jobs: [...]`.

## Job shape

```json
{
  "id": 2091062,
  "url": "https://remotive.com/remote-jobs/software-development/senior-...-2091062",
  "title": "Senior Product Engineer",
  "company_name": "Clipster",
  "category": "Software Development",
  "tags": ["fullstack"],
  "job_type": "full_time",
  "publication_date": "2026-07-13T07:05:10",
  "candidate_required_location": "Europe, UK",
  "salary": "",
  "description": "<p>HTML…</p>"
}
```

## Field mapping (→ portal contract)

| API field | Result field | Notes |
|-----------|--------------|-------|
| `id` | `id` | numeric; also the `detail` argument |
| `title` | `title` | |
| `company_name` | `company` | |
| `candidate_required_location` | `location` | region/timezone string |
| `publication_date` | `date` | ISO → `YYYY-MM-DD` |
| `url` | `url` | |
| — | `remote` | always `true` |
| `salary` | `salaryText` | free-text; `""` → `null` |
| `job_type` | `jobType` | |
| `category` | `category` | |
| `tags` | `tags` | |
| — | `visa` | derived from title+description+tags+location |
| — | `source` | constant `"remotive"` |

## Access

- Auth: none. ToS: public API. Attribution appreciated. Backoff on 429/5xx built in.
