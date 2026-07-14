// Data source: Arbeitnow public job-board API (JSON, no auth, no API key).
//   https://www.arbeitnow.com/api/job-board-api?page=<n>
// The free API has no server-side keyword search — it returns the latest jobs
// (100 per page). We fetch page(s) and filter client-side. Zero runtime deps.

export const API_URL = "https://www.arbeitnow.com/api/job-board-api"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

/** Fetch JSON with exponential backoff on 429/5xx. Returns null on a 404. */
export async function jsonFetch(url: string): Promise<any> {
  const maxRetries = 6
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      headers: {
        "User-Agent": UA,
        Accept: "application/json,text/plain,*/*",
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
    if (response.status === 404) return null
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }
  throw new Error("Request failed after max retries")
}

/** Raw job as returned by the Arbeitnow API. */
export interface ArbeitnowRaw {
  slug: string
  company_name: string
  title: string
  description: string
  remote: boolean
  url: string
  tags: string[]
  job_types: string[]
  location: string
  created_at: number // unix seconds
}

/** Normalized result conforming to the repo's portal output contract. */
export interface JobResult {
  id: string
  title: string
  company: string | null
  location: string | null
  date: string | null
  url: string
  remote: boolean
  visa: string | null // "sponsor" | "relocation" | null (best-effort hint)
  tags: string[]
  jobTypes: string[]
  source: "arbeitnow"
}

export interface JobDetail extends JobResult {
  description: string | null
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

/** Convert the HTML description to readable text, preserving line breaks. */
export function htmlToText(html: string): string {
  const withBreaks = html
    .replace(/<\s*br\s*\/?>/gi, "\n")
    .replace(/<\/(p|li|ul|ol|div|h\d)>/gi, "\n")
  return decodeHtmlEntities(withBreaks.replace(/<[^>]+>/g, " "))
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/ *\n */g, "\n")
    .trim()
}

/** ISO date (YYYY-MM-DD) from a unix-seconds timestamp. */
export function isoDate(unixSeconds: number): string | null {
  if (!unixSeconds || Number.isNaN(unixSeconds)) return null
  const d = new Date(unixSeconds * 1000)
  return Number.isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10)
}

/** Best-effort visa/relocation hint from the job's tags + description text. */
export function detectVisa(raw: ArbeitnowRaw): string | null {
  const hay = [...(raw.tags || []), raw.title || "", raw.description || ""]
    .join(" ")
    .toLowerCase()
  if (/\b(relocation|relocate|umzug)\b/.test(hay)) return "relocation"
  if (/\b(visa|sponsor|sponsorship|work permit)\b/.test(hay)) return "sponsor"
  return null
}

export function toResult(raw: ArbeitnowRaw): JobResult {
  return {
    id: raw.slug,
    title: raw.title || "(untitled)",
    company: raw.company_name || null,
    location: raw.location || null,
    date: isoDate(raw.created_at),
    url: raw.url,
    remote: Boolean(raw.remote),
    visa: detectVisa(raw),
    tags: raw.tags || [],
    jobTypes: raw.job_types || [],
    source: "arbeitnow",
  }
}

/** Case-insensitive keyword match across title, company, tags, and description. */
export function matchesQuery(raw: ArbeitnowRaw, query: string | undefined): boolean {
  if (!query) return true
  const hay = [raw.title, raw.company_name, (raw.tags || []).join(" "), raw.description]
    .join(" ")
    .toLowerCase()
  // all whitespace-separated terms must appear (AND semantics)
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((term) => hay.includes(term))
}
