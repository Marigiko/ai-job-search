// Data source: Landing.jobs public API v1 (JSON, no auth).
//   https://landing.jobs/api/v1/jobs
// EU-focused tech board; many roles are relocation/visa friendly (see the
// `relocation_paid` field). The feed returns the latest jobs (no server-side
// search), so we filter client-side. Zero runtime dependencies.

export const API_URL = "https://landing.jobs/api/v1/jobs"

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

export interface LjLocation {
  city?: string
  country_code?: string
}

export interface LjRaw {
  id?: number | string
  title?: string
  url?: string
  remote?: boolean
  relocation_paid?: boolean
  type?: string
  currency_code?: string
  gross_salary_low?: number
  gross_salary_high?: number
  published_at?: string
  tags?: string[]
  locations?: LjLocation[]
  main_requirements?: string
  nice_to_have?: string
  role_description?: string
  perks?: string
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
  salaryLow: number | null // annual gross, in `currency`
  salaryHigh: number | null
  currency: string | null
  tags: string[]
  source: "landingjobs"
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

export function isoDate(published: string | undefined): string | null {
  if (!published) return null
  const d = new Date(published)
  return Number.isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10)
}

/** Company is not an API field; derive it from the URL slug `/at/<company>/…`. */
export function companyFromUrl(url: string | undefined): string | null {
  if (!url) return null
  const m = url.match(/\/at\/([^/]+)\//)
  if (!m) return null
  return m[1]
    .split("-")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ")
}

export function detectVisa(raw: LjRaw): string | null {
  if (raw.relocation_paid) return "relocation"
  const hay = [raw.title || "", raw.role_description || "", raw.perks || "", (raw.tags || []).join(" ")]
    .join(" ")
    .toLowerCase()
  if (/\b(relocation|relocate)\b/.test(hay)) return "relocation"
  if (/\b(visa|sponsor|sponsorship|work permit)\b/.test(hay)) return "sponsor"
  return null
}

function nz(n: number | undefined): number | null {
  return n && n > 0 ? n : null
}

function fmtLocation(raw: LjRaw): string | null {
  const locs = raw.locations || []
  if (locs.length) {
    const parts = locs
      .map((l) => [l.city, l.country_code].filter(Boolean).join(", "))
      .filter(Boolean)
    if (parts.length) return parts.join(" | ")
  }
  return raw.remote ? "Remote" : null
}

export function toResult(raw: LjRaw): JobResult {
  return {
    id: String(raw.id ?? ""),
    title: raw.title || "(untitled)",
    company: companyFromUrl(raw.url),
    location: fmtLocation(raw),
    date: isoDate(raw.published_at),
    url: raw.url || "",
    remote: Boolean(raw.remote),
    visa: detectVisa(raw),
    salaryLow: nz(raw.gross_salary_low),
    salaryHigh: nz(raw.gross_salary_high),
    currency: raw.currency_code || null,
    tags: raw.tags || [],
    source: "landingjobs",
  }
}

/** Compose a readable description from the API's HTML/markdown text fields. */
export function composeDescription(raw: LjRaw): string | null {
  const parts: string[] = []
  if (raw.role_description) parts.push(htmlToText(raw.role_description))
  if (raw.main_requirements) parts.push("Requirements:\n" + htmlToText(raw.main_requirements))
  if (raw.nice_to_have) parts.push("Nice to have:\n" + htmlToText(raw.nice_to_have))
  if (raw.perks) parts.push("Perks:\n" + htmlToText(raw.perks))
  return parts.length ? parts.join("\n\n") : null
}

/** Case-insensitive keyword match across title, tags, requirements, description. */
export function matchesQuery(raw: LjRaw, query: string | undefined): boolean {
  if (!query) return true
  const hay = [raw.title, (raw.tags || []).join(" "), raw.main_requirements, raw.role_description]
    .join(" ")
    .toLowerCase()
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((term) => hay.includes(term))
}
