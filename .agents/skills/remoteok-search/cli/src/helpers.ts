// Data source: RemoteOK public API (JSON, no auth, no API key).
//   https://remoteok.com/api
// The response is an array whose FIRST element is a legal/metadata object
// (no job fields) — it must be skipped. Remaining elements are jobs. The API
// returns the latest jobs with no server-side search, so we filter client-side.
// Zero runtime dependencies.
//
// Attribution: RemoteOK's API terms ask consumers to link back to the job URL on
// Remote OK and mention Remote OK as the source. Keep the `url` field intact when
// presenting results.

export const API_URL = "https://remoteok.com/api"

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

/** Raw job as returned by the RemoteOK API (job elements, not the legal header). */
export interface RemoteOkRaw {
  id?: string
  slug?: string
  epoch?: number
  date?: string
  company?: string
  position?: string
  tags?: string[]
  description?: string
  location?: string
  url?: string
  apply_url?: string
  salary_min?: number
  salary_max?: number
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
  visa: string | null
  salaryMin: number | null // annual USD, per RemoteOK
  salaryMax: number | null
  applyUrl: string | null
  tags: string[]
  source: "remoteok"
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

/** A row is a real job (not the legal/metadata header) if it has a position. */
export function isJob(row: any): row is RemoteOkRaw {
  return row && typeof row === "object" && typeof row.position === "string" && row.position.length > 0
}

/** ISO date (YYYY-MM-DD): prefer the ISO `date` string, fall back to epoch. */
export function isoDate(raw: RemoteOkRaw): string | null {
  if (raw.date && /^\d{4}-\d{2}-\d{2}/.test(raw.date)) return raw.date.slice(0, 10)
  if (raw.epoch) {
    const d = new Date(raw.epoch * 1000)
    return Number.isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10)
  }
  return null
}

/** Best-effort visa/relocation hint from tags + position + description text. */
export function detectVisa(raw: RemoteOkRaw): string | null {
  const hay = [...(raw.tags || []), raw.position || "", raw.description || ""]
    .join(" ")
    .toLowerCase()
  if (/\b(relocation|relocate)\b/.test(hay)) return "relocation"
  if (/\b(visa|sponsor|sponsorship|work permit)\b/.test(hay)) return "sponsor"
  return null
}

function nz(n: number | undefined): number | null {
  return n && n > 0 ? n : null
}

export function toResult(raw: RemoteOkRaw): JobResult {
  const id = raw.id || raw.slug || ""
  return {
    id,
    title: raw.position || "(untitled)",
    company: raw.company || null,
    location: raw.location || null,
    date: isoDate(raw),
    url: raw.url || (raw.slug ? `https://remoteok.com/remote-jobs/${raw.slug}` : ""),
    remote: true, // every RemoteOK listing is remote
    visa: detectVisa(raw),
    salaryMin: nz(raw.salary_min),
    salaryMax: nz(raw.salary_max),
    applyUrl: raw.apply_url || null,
    tags: raw.tags || [],
    source: "remoteok",
  }
}

/** Case-insensitive keyword match across position, company, tags, description. */
export function matchesQuery(raw: RemoteOkRaw, query: string | undefined): boolean {
  if (!query) return true
  const hay = [raw.position, raw.company, (raw.tags || []).join(" "), raw.description]
    .join(" ")
    .toLowerCase()
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((term) => hay.includes(term))
}
