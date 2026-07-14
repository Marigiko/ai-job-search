// Data source: Jobicy public API v2 (JSON, no auth).
//   https://jobicy.com/api/v2/remote-jobs?count=<n>&tag=<kw>&geo=<region>&industry=<slug>
// Remote board with server-side keyword (tag), geo, and industry filters, and
// annual salary bands. `geo` covers regions like usa, new-zealand, europe.
// Zero runtime dependencies.

export const API_URL = "https://jobicy.com/api/v2/remote-jobs"

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

export interface JobicyRaw {
  id?: number | string
  url?: string
  jobSlug?: string
  jobTitle?: string
  companyName?: string
  jobIndustry?: string[] | string
  jobType?: string[] | string
  jobGeo?: string
  jobLevel?: string
  jobExcerpt?: string
  jobDescription?: string
  pubDate?: string
  salaryMin?: number
  salaryMax?: number
  salaryCurrency?: string
  salaryPeriod?: string
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
  salaryMin: number | null
  salaryMax: number | null
  salaryCurrency: string | null
  salaryPeriod: string | null
  level: string | null
  tags: string[]
  source: "jobicy"
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

function asArray(v: string[] | string | undefined): string[] {
  if (Array.isArray(v)) return v
  if (typeof v === "string" && v) return [v]
  return []
}

export function detectVisa(raw: JobicyRaw): string | null {
  const hay = [raw.jobTitle || "", raw.jobExcerpt || "", raw.jobDescription || "", asArray(raw.jobIndustry).join(" ")]
    .join(" ")
    .toLowerCase()
  if (/\b(relocation|relocate)\b/.test(hay)) return "relocation"
  if (/\b(visa|sponsor|sponsorship|work permit)\b/.test(hay)) return "sponsor"
  return null
}

function nz(n: number | undefined): number | null {
  return n && n > 0 ? n : null
}

export function toResult(raw: JobicyRaw): JobResult {
  return {
    id: String(raw.id ?? raw.jobSlug ?? ""),
    title: raw.jobTitle || "(untitled)",
    company: raw.companyName || null,
    location: raw.jobGeo || null,
    date: isoDate(raw.pubDate),
    url: raw.url || "",
    remote: true, // Jobicy is remote-only
    visa: detectVisa(raw),
    salaryMin: nz(raw.salaryMin),
    salaryMax: nz(raw.salaryMax),
    salaryCurrency: raw.salaryCurrency || null,
    salaryPeriod: raw.salaryPeriod || null,
    level: raw.jobLevel || null,
    tags: asArray(raw.jobIndustry),
    source: "jobicy",
  }
}

export function extractJobs(data: any): JobicyRaw[] {
  return data && Array.isArray(data.jobs) ? data.jobs : []
}

/** Rough monthly-USD estimate for a salary floor comparison (annual/12, monthly as-is). */
export function monthlyEstimate(r: JobResult): number | null {
  if (r.salaryMax === null) return null
  const per = (r.salaryPeriod || "").toLowerCase()
  if (per.includes("year") || per.includes("annual")) return Math.round(r.salaryMax / 12)
  if (per.includes("month")) return r.salaryMax
  if (per.includes("hour")) return r.salaryMax * 160
  return Math.round(r.salaryMax / 12) // Jobicy salaries are annual by default
}
