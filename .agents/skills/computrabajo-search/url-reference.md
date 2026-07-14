# Computrabajo reference

Data source: Computrabajo public search/offer HTML pages. No auth. Personal use only (ToS).

## URLs

```
Search:  https://<country>.computrabajo.com/trabajo-de-<slug>?p=<page>
Offer:   https://<country>.computrabajo.com/ofertas-de-trabajo/<offer-slug>-<HEXID>
```

- `<country>`: `ar` (default), `mx`, `cl`, `pe`, `co`, `uy`, …
- `<slug>`: the query, slugified (spaces → `-`, accents stripped). Pagination via `?p=<n>`.
- No server-side keyword API — the query is baked into the URL slug.

## Search card markup (per `<article class="box_offer …" data-id='HEXID'>`)

| Element | Selector | → field |
|---------|----------|---------|
| Title + link | `a.js-o-link[href]` | `title`, `url` (relative → prefixed) |
| Company | `a[offer-grid-article-company-url]` text | `company` |
| Location | `p.fs16.fc_base.mt5 > span.mr10` | `location` |
| Modality | `span > i_home_office` sibling text | `remote` (contains "remoto") |
| Posted | `p.fs13.fc_aux` | `posted` (raw) → `date` (approx ISO) |
| Id | `data-id` | `id` |

## Offer detail

- The full description lives under `<h3>Descripción de la oferta</h3>` → a `div.mbB` (tags: salary
  "A convenir"/contract/modality) + `p.mbB` (the text). `parseDetailDescription` captures that block.

## Field mapping (→ portal contract)

`id, title, company, location, date` (approx from `posted`), `url` + extras `remote`, `visa`
(text hint), `posted` (raw relative), `source: "computrabajo"`.

## Access

- Auth: none (public pages). Anti-bot: none observed on `.ar` search pages (unlike Bumeran → Cloudflare).
- ToS: automated access may be disallowed → **personal-use-only** banner in SKILL.md; keep volume low.
- Brittleness: HTML scraping; markup changes will break selectors (JSON-API portals are more robust).
