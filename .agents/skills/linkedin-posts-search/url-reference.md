# LinkedIn public posts reference

Data source: public LinkedIn post permalinks. No authentication. Personal use only (LinkedIn ToS).

## URL

```
https://www.linkedin.com/posts/<author-slug>_<hashtags>-activity-<ACTIVITY_ID>-<xxxx>
```

- Logged-out these return **HTTP 200** with Open Graph meta + body (observed for hiring posts).
- The **feed** and keyword search are behind the authenticated Voyager API — NOT used here.

## What is parsed

| Source in HTML | → field |
|----------------|---------|
| `og:title` ("Author on LinkedIn" / "#tags \| Company") | `author` |
| `og:description` / `description` | `text` (post snippet) |
| `activity-<ID>` in the URL | `id`, and `date` = `new Date(Number(BigInt(ID) >> 22n))` |
| `mailto:` + inline addresses (de-obfuscated) | `emails`, `applyEmail` (first) |
| synthesized (first line of text) | `title` |

## Email de-obfuscation

Before matching `[\w.%+-]+@[\w.-]+\.\w{2,}`, the text is normalized:
`&#64;`→`@`, `[at]`/`(at)`/` at `→`@`, `[dot]`/`(dot)`→`.`. Asset filenames (`*.png`) and infra
domains (`licdn.com`, `linkedin.com`, `sentry`, …) are filtered out.

## Reliability

- Live `extract` depends on LinkedIn serving the public post (it usually does for hiring posts).
  If a post is gated, use `parse --text "<pasted post>"` — fully offline, always works.
- The date is derived from the id, so it is available even when only the URL is known.
