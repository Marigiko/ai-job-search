# Jobicy API reference

Data source: the public Jobicy API v2. No authentication, no API key.

## Endpoint

```
GET https://jobicy.com/api/v2/remote-jobs?count=<n>&tag=<kw>&geo=<region>&industry=<slug>
```

- `tag` = keyword filter, `geo` = region (`usa`, `new-zealand`, `europe`, `canada`, `australia`, …),
  `count` ≤ 50. Response: `{ jobs: [...], appliedFilters, jobCount }`.

## Job shape

```json
{
  "id": 149243,
  "url": "https://jobicy.com/jobs/149243-senior-backend-developer",
  "jobSlug": "senior-backend-developer",
  "jobTitle": "Senior Backend Developer",
  "companyName": "Mindrift",
  "jobIndustry": ["Software Engineering"],
  "jobType": ["Full-Time"],
  "jobGeo": "USA",
  "jobLevel": "Senior",
  "jobExcerpt": "…",
  "jobDescription": "<p>HTML…</p>",
  "pubDate": "2026-07-13T14:26:05+00:00",
  "salaryMin": 120000, "salaryMax": 180000, "salaryCurrency": "USD", "salaryPeriod": "yearly"
}
```

## Field mapping (→ portal contract)

| API field | Result field | Notes |
|-----------|--------------|-------|
| `id` | `id` | also the `detail` argument |
| `jobTitle` | `title` | |
| `companyName` | `company` | |
| `jobGeo` | `location` | target region (remote role) |
| `pubDate` | `date` | ISO → `YYYY-MM-DD` |
| `url` | `url` | |
| — | `remote` | always `true` |
| `salaryMin`/`salaryMax` | `salaryMin`/`salaryMax` | annual; `0`→`null` |
| `salaryCurrency`/`salaryPeriod` | `salaryCurrency`/`salaryPeriod` | |
| `jobLevel` | `level` | |
| `jobIndustry` | `tags` | |
| — | `visa` | derived from title+excerpt+description+industry |
| — | `source` | constant `"jobicy"` |

## Access

- Auth: none. ToS: public API, attribution appreciated. Backoff on 429/5xx built in.
- Region coverage (`geo`) makes this the repo's primary **USA / New Zealand / Europe** remote portal.
