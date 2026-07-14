# RemoteOK API reference

Data source: the public RemoteOK API. No authentication, no API key.

## Endpoint

```
GET https://remoteok.com/api
```

- Returns a JSON **array**. The **first element is a legal/metadata object** (`legal`,
  `last_updated`) and must be skipped. Remaining elements are jobs, newest first (~100).
- Requires a normal browser `User-Agent` (the CLI sets one) or it may 403.
- No server-side search/pagination in the public feed — filtering is client-side.

## Job element shape

```json
{
  "slug": "remote-backend-developer-acme-1134769",
  "id": "1134769",
  "epoch": 1783951039,
  "date": "2026-07-13T13:57:19+00:00",
  "company": "Acme",
  "position": "Backend Developer",
  "tags": ["python", "backend"],
  "description": "<p>HTML description…</p>",
  "location": "Worldwide",
  "apply_url": "https://remoteok.com/remote-jobs/…",
  "salary_min": 60000,
  "salary_max": 90000,
  "url": "https://remoteok.com/remote-jobs/…"
}
```

## Field mapping (→ portal contract)

| API field | Result field | Notes |
|-----------|--------------|-------|
| `id` (or `slug`) | `id` | numeric id preferred; `detail` accepts id/slug/url |
| `position` | `title` | |
| `company` | `company` | `null` if empty |
| `location` | `location` | `null` if empty |
| `date` / `epoch` | `date` | ISO date preferred, else epoch → `YYYY-MM-DD` |
| `url` | `url` | preserve (attribution) |
| `apply_url` | `applyUrl` | |
| `salary_min`/`salary_max` | `salaryMin`/`salaryMax` | annual USD; `0`/absent → `null` |
| — | `remote` | always `true` |
| — | `visa` | derived from text: `sponsor`/`relocation`/`null` |
| `tags` | `tags` | |
| — | `source` | constant `"remoteok"` |

## Access

- `robots.txt`: `/api` is a documented public JSON API.
- Auth: none.
- ToS: attribution requested (link back to the job `url`, credit Remote OK). No personal-use
  restriction like LinkedIn; keep request volume reasonable (backoff on 429/5xx is built in).
