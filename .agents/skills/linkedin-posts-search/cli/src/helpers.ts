// Data source: public LinkedIn post permalinks (https://www.linkedin.com/posts/<slug>).
// Logged-out these pages return HTTP 200 with Open Graph meta (og:title = author/
// company, og:description = post text snippet) and the post body — enough to
// extract an apply-by-email address. Zero runtime dependencies.
//
// ⚠️ Personal use only. Automated access to LinkedIn is against its Terms of
// Service. This skill only fetches PUBLIC post permalinks you already have (found
// via WebSearch, not by crawling the feed), and parses/pastes their text. Keep
// volume low; run it on your own responsibility. Feed keyword search requires a
// logged-in session and is intentionally NOT done here (see the authenticated
// mode note in SKILL.md).

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

/** Fetch HTML with exponential backoff on 429/5xx. Returns "" on a 404. */
export async function htmlFetch(url: string): Promise<string> {
  const maxRetries = 6
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      headers: {
        "User-Agent": UA,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
      },
      redirect: "follow",
    })
    if (response.status === 429 || response.status >= 500) {
      if (attempt === maxRetries) {
        throw new Error(`Request failed: ${response.status} ${response.statusText}`)
      }
      const jitter = Math.floor(Math.random() * 500)
      await new Promise((r) => setTimeout(r, delay + jitter))
      delay = Math.min(delay * 2, 8000)
      continue
    }
    if (response.status === 404) return ""
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }
    return response.text()
  }
  throw new Error("Request failed after max retries")
}

export interface PostResult {
  id: string
  title: string
  company: string | null
  location: string | null
  date: string | null
  url: string
  applyEmail: string | null
  emails: string[]
  author: string | null
  text: string | null
  source: "linkedin-post"
}

function decodeHtmlEntities(text: string): string {
  return text
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, d) => {
      const cp = parseInt(d, 10)
      return cp >= 0 && cp <= 0x10ffff ? String.fromCodePoint(cp) : ""
    })
    .replace(/&#[xX]([0-9a-fA-F]+);/g, (_, h) => {
      const cp = parseInt(h, 16)
      return cp >= 0 && cp <= 0x10ffff ? String.fromCodePoint(cp) : ""
    })
    .replace(/&nbsp;/g, " ")
}

function meta(html: string, prop: string): string | null {
  const m =
    html.match(new RegExp(`<meta[^>]+property="${prop}"[^>]+content="([^"]*)"`, "i")) ||
    html.match(new RegExp(`<meta[^>]+content="([^"]*)"[^>]+property="${prop}"`, "i")) ||
    html.match(new RegExp(`<meta[^>]+name="${prop}"[^>]+content="([^"]*)"`, "i"))
  return m ? decodeHtmlEntities(m[1]) : null
}

/** The activity/ugcPost numeric id encodes the creation time in its high bits. */
export function activityIdFromUrl(url: string): string | null {
  const m = url.match(/(?:activity|ugcPost)[:-](\d{15,})/) || url.match(/(\d{18,})/)
  return m ? m[1] : null
}

export function dateFromActivityId(id: string | null): string | null {
  if (!id) return null
  try {
    const ms = Number(BigInt(id) >> 22n)
    if (!ms || ms < 1_000_000_000_000 || ms > Date.now() + 86_400_000) return null
    return new Date(ms).toISOString().slice(0, 10)
  } catch {
    return null
  }
}

/** De-obfuscate common email spellings, then extract addresses. */
export function extractEmails(text: string): string[] {
  const normalized = decodeHtmlEntities(text)
    .replace(/&#0*64;/g, "@")
    .replace(/\s*\[\s*at\s*\]\s*/gi, "@")
    .replace(/\s*\(\s*at\s*\)\s*/gi, "@")
    .replace(/\s+at\s+(?=[a-z0-9.-]+\.[a-z]{2,})/gi, "@")
    .replace(/\s*\[\s*dot\s*\]\s*/gi, ".")
    .replace(/\s*\(\s*dot\s*\)\s*/gi, ".")
  const found = normalized.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g) || []
  const junk = /\.(png|jpe?g|gif|svg|webp|css|js)$/i
  const infra = /(sentry|licdn|linkedin|wikimedia|schema\.org|w3\.org|example\.(com|org|net))/i
  const seen = new Set<string>()
  const out: string[] = []
  for (const e of found) {
    const lower = e.toLowerCase()
    if (junk.test(lower) || infra.test(lower.split("@")[1] || "")) continue
    if (!seen.has(lower)) {
      seen.add(lower)
      out.push(e)
    }
  }
  return out
}

/** Split "Author on LinkedIn: text" / "#tags | Company" OG titles into author/company. */
function authorFromOgTitle(ogTitle: string | null): string | null {
  if (!ogTitle) return null
  const t = ogTitle
  const lower = t.toLowerCase()
  // Check the "… posted on LinkedIn" / "posted images on LinkedIn" variants first.
  const postedIdx = lower.search(/\s+posted\b/)
  if (postedIdx > 0 && lower.includes("on linkedin")) return t.slice(0, postedIdx).trim()
  const onIdx = lower.indexOf(" on linkedin")
  if (onIdx > 0) return t.slice(0, onIdx).trim()
  const pipe = t.lastIndexOf("|")
  if (pipe > 0) return t.slice(pipe + 1).trim() // "#tags | Company"
  return t.trim() || null
}

function synthTitle(text: string | null, author: string | null): string {
  if (text) {
    const firstLine = text.split(/[\n.!?]/)[0].trim()
    if (firstLine) return firstLine.slice(0, 100)
  }
  return author ? `Post by ${author}` : "LinkedIn post"
}

/** Build a PostResult from fetched post HTML. */
export function buildFromHtml(html: string, url: string): PostResult {
  const ogTitle = meta(html, "og:title")
  const ogDesc = meta(html, "og:description") || meta(html, "description")
  const author = authorFromOgTitle(ogTitle)
  const text = ogDesc || null
  const id = activityIdFromUrl(url)
  const emails = extractEmails(html)
  return {
    id: id || url,
    title: synthTitle(text, author),
    company: null,
    location: null,
    date: dateFromActivityId(id),
    url: url.split("?")[0],
    applyEmail: emails[0] ?? null,
    emails,
    author,
    text,
    source: "linkedin-post",
  }
}

/** Build a PostResult from pasted post text (no network) — the reliable path. */
export function buildFromText(text: string, url?: string): PostResult {
  const emails = extractEmails(text)
  const id = url ? activityIdFromUrl(url) : null
  return {
    id: id || (url ? url.split("?")[0] : "pasted-post"),
    title: synthTitle(text, null),
    company: null,
    location: null,
    date: dateFromActivityId(id),
    url: url ? url.split("?")[0] : "",
    applyEmail: emails[0] ?? null,
    emails,
    author: null,
    text: text.trim().slice(0, 4000),
    source: "linkedin-post",
  }
}
