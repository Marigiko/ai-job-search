// Data source: Remotive public API (JSON, no auth).
//   https://remotive.com/api/remote-jobs?search=<kw>&limit=<n>
// Remote-only board with server-side keyword search. Zero runtime dependencies.

export const API_URL = "https://remotive.com/api/remote-jobs"

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

export interface RemotiveRaw {
  id?: number | string
  url?: string
  title?: string
  company_name?: string
  category?: string
  tags?: string[]
  job_type?: string
  publication_date?: string
  candidate_required_location?: string
  salary?: string
  description?: string
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
  salaryText: string | null
  jobType: string | null
  category: string | null
  tags: string[]
  source: "remotive"
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
  const d = new Date(published.replace(" ", "T"))
  return Number.isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10)
}

export function detectVisa(raw: RemotiveRaw): string | null {
  const hay = [raw.title || "", raw.description || "", (raw.tags || []).join(" "), raw.candidate_required_location || ""]
    .join(" ")
    .toLowerCase()
  if (/\b(relocation|relocate)\b/.test(hay)) return "relocation"
  if (/\b(visa|sponsor|sponsorship|work permit)\b/.test(hay)) return "sponsor"
  return null
}

export function toResult(raw: RemotiveRaw): JobResult {
  return {
    id: String(raw.id ?? ""),
    title: raw.title || "(untitled)",
    company: raw.company_name || null,
    location: raw.candidate_required_location || null,
    date: isoDate(raw.publication_date),
    url: raw.url || "",
    remote: true, // Remotive is remote-only
    visa: detectVisa(raw),
    salaryText: raw.salary ? raw.salary : null,
    jobType: raw.job_type || null,
    category: raw.category || null,
    tags: raw.tags || [],
    source: "remotive",
  }
}

/** Extract the jobs array, skipping Remotive's warning/legal/meta keys. */
export function extractJobs(data: any): RemotiveRaw[] {
  return data && Array.isArray(data.jobs) ? data.jobs : []
}
