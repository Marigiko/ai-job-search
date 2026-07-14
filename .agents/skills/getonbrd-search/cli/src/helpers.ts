// Data source: Get on Board (getonbrd.com) public API v0 (JSON:API-style).
//   https://www.getonbrd.com/api/v0/search/jobs?query=<kw>&remote=<bool>&page=<n>&per_page=<n>
// LatAm + remote tech board. Search is server-side (real query + pagination).
// Salaries are MONTHLY USD. Zero runtime dependencies.
//
// JSON:API caveat: `company` and `seniority` come as relationship references
// (`{ data: { id, type } }`) without inline labels. We resolve company names via
// /companies/:id (cached per run) and seniority via the /seniorities catalog
// (fetched once). `category_name` and salaries are inline.

export const API_BASE = "https://www.getonbrd.com/api/v0"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

/** Fetch JSON with exponential backoff on 429/5xx. Returns null on 401/404. */
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
    if (response.status === 401 || response.status === 404) return null
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }
  throw new Error("Request failed after max retries")
}

interface Ref {
  data?: { id?: number | string; type?: string } | null
}

export interface GobAttributes {
  title?: string
  description?: string
  remote?: boolean
  remote_modality?: string
  countries?: string[]
  min_salary?: number
  max_salary?: number
  published_at?: number
  category_name?: string
  perks?: string
  seniority?: Ref
  company?: Ref
}

export interface GobJob {
  id: string
  attributes?: GobAttributes
  links?: { public_url?: string }
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
  salaryMin: number | null // MONTHLY USD
  salaryMax: number | null
  seniority: string | null
  category: string | null
  source: "getonbrd"
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

export function isoDate(unixSeconds: number | undefined): string | null {
  if (!unixSeconds || Number.isNaN(unixSeconds)) return null
  const d = new Date(unixSeconds * 1000)
  return Number.isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10)
}

export function detectVisa(a: GobAttributes): string | null {
  const hay = [a.title || "", a.description || "", a.perks || "", (a.countries || []).join(" ")]
    .join(" ")
    .toLowerCase()
  if (/\b(relocation|relocate|relocaci)\b/.test(hay)) return "relocation"
  if (/\b(visa|sponsor|sponsorship|work permit)\b/.test(hay)) return "sponsor"
  return null
}

function nz(n: number | undefined): number | null {
  return n && n > 0 ? n : null
}

/** Map the raw job + resolved labels to the portal contract. */
export function toResult(
  job: GobJob,
  companyName: string | null,
  seniorityName: string | null,
): JobResult {
  const a = job.attributes || {}
  const countries = a.countries || []
  const location = countries.length ? countries.join(", ") : a.remote ? "Remote" : null
  return {
    id: job.id,
    title: a.title || "(untitled)",
    company: companyName,
    location,
    date: isoDate(a.published_at),
    url: job.links?.public_url || `https://www.getonbrd.com/jobs/${job.id}`,
    remote: Boolean(a.remote),
    visa: detectVisa(a),
    salaryMin: nz(a.min_salary),
    salaryMax: nz(a.max_salary),
    seniority: seniorityName,
    category: a.category_name || null,
    source: "getonbrd",
  }
}

// --- Relationship resolution (cached per process run) ------------------------

const companyCache = new Map<string, string | null>()
let seniorityMap: Map<string, string> | null = null

export async function resolveCompany(ref: Ref | undefined): Promise<string | null> {
  const id = ref?.data?.id
  if (id === undefined || id === null) return null
  const key = String(id)
  if (companyCache.has(key)) return companyCache.get(key) ?? null
  try {
    const data = await jsonFetch(`${API_BASE}/companies/${key}`)
    const name = data?.data?.attributes?.name ?? null
    companyCache.set(key, name)
    return name
  } catch {
    companyCache.set(key, null)
    return null
  }
}

export async function getSeniorityMap(): Promise<Map<string, string>> {
  if (seniorityMap) return seniorityMap
  const map = new Map<string, string>()
  try {
    const data = await jsonFetch(`${API_BASE}/seniorities`)
    for (const s of data?.data || []) {
      const label = s?.attributes?.name ?? s?.attributes?.label
      if (s?.id !== undefined && label) map.set(String(s.id), label)
    }
  } catch {
    /* leave the map empty; seniority stays null */
  }
  seniorityMap = map
  return map
}

export function seniorityLabel(ref: Ref | undefined, map: Map<string, string>): string | null {
  const id = ref?.data?.id
  if (id === undefined || id === null) return null
  return map.get(String(id)) ?? null
}
