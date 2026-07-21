// Shared helpers for linkedin-recruiter-cli.
// Data source: public search engines (Google/Bing) -> LinkedIn post permalinks.
// Personal use only (LinkedIn ToS). Does not authenticate against LinkedIn.

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

export function writeOutput(payload: unknown): void {
  process.stdout.write(JSON.stringify(payload, null, 2) + "\n")
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
  source: "linkedin-recruiter-post"
}

export function jsonSummary(count: number) {
  return { meta: { count }, results: [] }
}

function decodeHtmlEntities(text: string): string {
  return text
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#(\d+);/g, (_, d) => {
      const cp = parseInt(d, 10)
      return cp >= 0 && cp <= 0x10ffff ? String.fromCodePoint(cp) : ""
    })
    .replace(/&nbsp;/g, " ")
}

const LINKEDIN_RE =
  /https?:\/\/(?:www\.)?linkedin\.com\/(?:posts|feed\/update\/urn:li:activity:)[^\s"'<>]+/

export function extractLinkedinUrls(text: string): string[] {
  const found = text.match(new RegExp(LINKEDIN_RE.source, "g")) || []
  const seen = new Set<string>()
  const out: string[] = []
  for (const u of found) {
    const clean = u.replace(/[).,;]+$/g, "")
    const base = clean.split("?")[0]
    if (!seen.has(base)) {
      seen.add(base)
      out.push(clean)
    }
  }
  return out
}

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

export function synthTitle(text: string | null, fallback: string): string {
  if (text) {
    const firstLine = text.split(/[\n.!?]/)[0].trim()
    if (firstLine) return firstLine.slice(0, 120)
  }
  return fallback
}

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

export function buildFromPostUrl(url: string, snippet: string | null): PostResult {
  const id = activityIdFromUrl(url)
  const emails = snippet ? extractEmails(snippet) : []
  return {
    id: id || url,
    title: synthTitle(snippet, url),
    company: null,
    location: null,
    date: dateFromActivityId(id),
    url: url.split("?")[0],
    applyEmail: emails[0] ?? null,
    emails,
    author: null,
    text: snippet ? snippet.trim().slice(0, 4000) : null,
    source: "linkedin-recruiter-post",
  }
}
