# The Muse API reference

Data source: The Muse public jobs API. No authentication, no API key.

## Endpoints

```
GET https://www.themuse.com/api/public/jobs?category=<>&location=<>&level=<>&page=<n>
GET https://www.themuse.com/api/public/jobs/<id>        # per-job detail
```

- `location`, `category`, `level`, `page` are server-side. **No keyword param** — keyword filtering
  is client-side. Response: `{ page, page_count, total, results: [...] }`.
- Location is a city/region string: `"New York, NY"`, `"Auckland, New Zealand"`,
  `"London, United Kingdom"`, `"Flexible / Remote"`.

## Job shape

```json
{
  "id": 21610367,
  "name": "Senior Backend Engineer",
  "company": { "name": "Bank of America" },
  "locations": [{ "name": "New York, NY" }],
  "categories": [{ "name": "Software Engineering" }],
  "levels": [{ "name": "Senior Level" }],
  "publication_date": "2026-07-07T19:16:09Z",
  "contents": "<p>HTML…</p>",
  "refs": { "landing_page": "https://www.themuse.com/jobs/…" }
}
```

## Field mapping (→ portal contract)

| API field | Result field | Notes |
|-----------|--------------|-------|
| `id` | `id` | numeric; the `detail` argument |
| `name` | `title` | |
| `company.name` | `company` | |
| `locations[].name` | `location` | joined; remote if any is "Flexible / Remote" |
| `publication_date` | `date` | ISO → `YYYY-MM-DD` |
| `refs.landing_page` | `url` | |
| location "Flexible / Remote" | `remote` | boolean |
| `levels[0].name` | `level` | |
| `categories[0].name` | `category` | |
| — | `visa` | derived from name+contents |
| — | `source` | constant `"themuse"` |

## Access

- Auth: none. ToS: public API (rate-limited generously). Backoff on 429/5xx built in.
- Regional role: primary **USA** portal; strong **New Zealand / UK / Europe** via `location`.
