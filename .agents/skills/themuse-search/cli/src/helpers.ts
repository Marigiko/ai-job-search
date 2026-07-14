// Data source: The Muse public jobs API (JSON, no auth, no key).
//   https://www.themuse.com/api/public/jobs?category=<>&location=<>&level=<>&page=<n>
//   https://www.themuse.com/api/public/jobs/<id>            (per-job detail)
// US-strong but global (location is a city/region string, e.g. "New York, NY",
// "Auckland, New Zealand", "London, United Kingdom", "Flexible / Remote").
// No keyword param in the public API, so keyword filtering is client-side.
// Zero runtime dependencies.

export const API_BASE = "https://www.themuse.com/api/public/jobs"

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

export interface MuseRaw {
  id?: number | string
  name?: string
  company?: { name?: string }
  locations?: { name?: string }[]
  categories?: { name?: string }[]
  levels?: { name?: string }[]
  tags?: { name?: string }[]
  publication_date?: string
  contents?: string
  refs?: { landing_page?: string }
}

export interface JobResult {
  id: string
  title: string
  company: string | null
  location: string | null
  date: string | null
  url: string
  remote: boolean
  visa: string | null
  level: string | null
  category: string | null
  source: "themuse"
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

export function isoDate(pub: string | undefined): string | null {
  if (!pub) return null
  const d = new Date(pub)
  return Number.isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10)
}

function locationString(raw: MuseRaw): { text: string | null; remote: boolean } {
  const names = (raw.locations || []).map((l) => l.name).filter(Boolean) as string[]
  const remote = names.some((n) => /flexible|remote/i.test(n))
  return { text: names.length ? names.join(" | ") : null, remote }
}

export function detectVisa(raw: MuseRaw): string | null {
  const hay = [raw.name || "", raw.contents || ""].join(" ").toLowerCase()
  if (/\b(relocation|relocate)\b/.test(hay)) return "relocation"
  if (/\b(visa|sponsor|sponsorship|work permit)\b/.test(hay)) return "sponsor"
  return null
}

export function toResult(raw: MuseRaw): JobResult {
  const { text, remote } = locationString(raw)
  return {
    id: String(raw.id ?? ""),
    title: raw.name || "(untitled)",
    company: raw.company?.name || null,
    location: text,
    date: isoDate(raw.publication_date),
    url: raw.refs?.landing_page || "",
    remote,
    visa: detectVisa(raw),
    level: (raw.levels || [])[0]?.name || null,
    category: (raw.categories || [])[0]?.name || null,
    source: "themuse",
  }
}

/** Client-side keyword match (The Muse API has no keyword param). */
export function matchesQuery(raw: MuseRaw, query: string | undefined): boolean {
  if (!query) return true
  const hay = [
    raw.name,
    raw.company?.name,
    (raw.categories || []).map((c) => c.name).join(" "),
    raw.contents,
  ]
    .join(" ")
    .toLowerCase()
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((term) => hay.includes(term))
}
