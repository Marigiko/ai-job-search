# We Work Remotely RSS reference

Data source: We Work Remotely public RSS category feeds. No authentication, no API key.

## Feeds

```
GET https://weworkremotely.com/categories/<category-slug>.rss
```

Category slugs used by this skill (`--category` → slug):

| `--category` | feed slug |
|--------------|-----------|
| programming (default) | remote-programming-jobs |
| full-stack | remote-full-stack-programming-jobs |
| back-end | remote-back-end-programming-jobs |
| front-end | remote-front-end-programming-jobs |
| devops | remote-devops-sysadmin-jobs |
| design | remote-design-jobs |
| product | remote-product-jobs |
| customer-support | remote-customer-support-jobs |
| sales | remote-sales-and-marketing-jobs |
| all | remote-jobs |

Feeds list the latest jobs (~25–50 per category). No server-side search — filter client-side.

## `<item>` shape

```xml
<item>
  <title>Company Name: Position Title</title>
  <link>https://weworkremotely.com/remote-jobs/company-position-slug</link>
  <guid>https://weworkremotely.com/remote-jobs/company-position-slug</guid>
  <pubDate>Tue, 30 Jun 2026 20:31:08 +0000</pubDate>
  <region>Anywhere in the World</region>
  <category>Full-Stack Programming</category>
  <description><![CDATA[ entity-escaped HTML description ]]></description>
</item>
```

## Field mapping (→ portal contract)

| RSS field | Result field | Notes |
|-----------|--------------|-------|
| `link` (slug) | `id` | slug after `/remote-jobs/` |
| `title` (after `: `) | `title` | title is `"Company: Position"` |
| `title` (before `: `) | `company` | `null` if no `": "` prefix |
| `region` | `location` | e.g. "Anywhere in the World", "USA Only" |
| `pubDate` | `date` | RFC-822 → `YYYY-MM-DD` |
| `link` | `url` | canonical job page |
| — | `remote` | always `true` |
| — | `visa` | derived from title+description+region text |
| `category` | `category` | WWR category label |
| — | `source` | constant `"weworkremotely"` |

## Access

- `robots.txt`: RSS feeds are public and intended for syndication.
- Auth: none.
- ToS: public RSS. Keep request volume reasonable (backoff on 429/5xx built in).
