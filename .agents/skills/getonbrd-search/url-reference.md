# Get on Board API reference

Data source: the public Get on Board API v0. No authentication for search.

## Endpoints

```
GET https://www.getonbrd.com/api/v0/search/jobs?query=<kw>&remote=<bool>&page=<n>&per_page=<n>
GET https://www.getonbrd.com/api/v0/companies/<id>     # resolve company name
GET https://www.getonbrd.com/api/v0/seniorities        # id -> label catalog
```

- Search is **server-side** (real `query`, `remote`, pagination via `meta.total_pages`).
- The per-job endpoint `GET /api/v0/jobs/<slug>` requires auth (**401**) — not used. The full
  description is available inline in search results, so `detail` re-queries search.

## Job shape (search `data[]`)

```json
{
  "id": "senior-backend-developer-acme-santiago-e811",
  "type": "job",
  "attributes": {
    "title": "Senior Backend Developer",
    "description": "<p>HTML…</p>",
    "remote": true,
    "remote_modality": "remote_local",
    "countries": ["Remote"],
    "min_salary": 2700,
    "max_salary": 2900,
    "published_at": 1784039034,
    "category_name": "Programming",
    "seniority": { "data": { "id": 4, "type": "seniority" } },
    "company":   { "data": { "id": 19970, "type": "company" } }
  },
  "links": { "public_url": "https://www.getonbrd.com/jobs/…" }
}
```

## Field mapping (→ portal contract)

| API field | Result field | Notes |
|-----------|--------------|-------|
| `id` | `id` | slug; also the `detail` argument |
| `attributes.title` | `title` | |
| `company.data.id` → `/companies/:id` `.name` | `company` | resolved + cached; `null` on failure |
| `countries` (or Remote) | `location` | joined; `"Remote"` when remote and no countries |
| `published_at` | `date` | unix seconds → `YYYY-MM-DD` |
| `links.public_url` | `url` | |
| `remote` | `remote` | boolean |
| `min_salary`/`max_salary` | `salaryMin`/`salaryMax` | **monthly USD**; `0`/absent → `null` |
| `seniority.data.id` → `/seniorities` | `seniority` | label (Sin experiencia/Junior/Semi Senior/Senior/Expert) |
| `category_name` | `category` | inline |
| — | `visa` | derived from title+description+perks+countries |
| — | `source` | constant `"getonbrd"` |

## Access

- Auth: none for `search` and `companies`/`seniorities`. `jobs/:id` is auth-walled (avoided).
- ToS: public API. Keep request volume reasonable; company lookups are cached per run (backoff on 429/5xx).
