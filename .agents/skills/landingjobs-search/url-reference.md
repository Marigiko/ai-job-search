# Landing.jobs API reference

Data source: the public Landing.jobs API v1. No authentication, no API key.

## Endpoint

```
GET https://landing.jobs/api/v1/jobs[?page=<n>]
```

- Returns a JSON **array** of the latest jobs (~50). No server-side keyword search — filter client-side.
- `?page=<n>` paginates.

## Job shape

```json
{
  "id": 19066,
  "title": "Senior Java Software Developer",
  "url": "https://landing.jobs/at/inscale/senior-java-software-developer-in-lisbon-2025",
  "remote": false,
  "relocation_paid": false,
  "type": "Full-time",
  "currency_code": "EUR",
  "gross_salary_low": 50000,
  "gross_salary_high": 67000,
  "published_at": "2025-02-26T09:38:38.127Z",
  "tags": ["Java", "Spring Boot"],
  "locations": [{ "city": "Lisbon", "country_code": "PT" }],
  "main_requirements": "…", "nice_to_have": "…", "role_description": "…", "perks": "…"
}
```

## Field mapping (→ portal contract)

| API field | Result field | Notes |
|-----------|--------------|-------|
| `id` | `id` | numeric; also the `detail` argument |
| `title` | `title` | |
| `url` slug `/at/<company>/` | `company` | **derived** (no company field); title-cased slug |
| `locations[]` (city, country_code) | `location` | joined; `"Remote"` when remote & no locations |
| `published_at` | `date` | ISO → `YYYY-MM-DD` |
| `url` | `url` | canonical job page |
| `remote` | `remote` | boolean |
| `relocation_paid` / text | `visa` | `relocation` if `relocation_paid`, else text hint / `null` |
| `gross_salary_low`/`high` | `salaryLow`/`salaryHigh` | annual gross in `currency`; `0`→`null` |
| `currency_code` | `currency` | mostly EUR |
| `tags` | `tags` | |
| — | `source` | constant `"landingjobs"` |
| `role_description`+`main_requirements`+`nice_to_have`+`perks` | `description` (detail) | composed + HTML-stripped |

## Access

- `robots.txt`: `/api/v1/` is a public JSON API.
- Auth: none.
- ToS: public API. Keep request volume reasonable (backoff on 429/5xx built in).
