// Data source: We Work Remotely public RSS category feeds (XML, no auth).
//   https://weworkremotely.com/categories/<category>.rss
// Feeds list the latest remote jobs; there is no server-side keyword search, so
// we parse the feed and filter client-side. Zero runtime dependencies (regex XML
// parsing — the RSS is shallow and stable).

export const FEED_BASE = "https://weworkremotely.com/categories"

/** Known category feed slugs (pass one via --category). */
export const CATEGORIES: Record<string, string> = {
  programming: "remote-programming-jobs",
  "full-stack": "remote-full-stack-programming-jobs",
  "back-end": "remote-back-end-programming-jobs",
  "front-end": "remote-front-end-programming-jobs",
  devops: "remote-devops-sysadmin-jobs",
  design: "remote-design-jobs",
  product: "remote-product-jobs",
  "customer-support": "remote-customer-support-jobs",
  sales: "remote-sales-and-marketing-jobs",
  all: "remote-jobs",
}

export function feedUrl(category: string): string {
  const slug = CATEGORIES[category] ?? CATEGORIES.programming
  return `${FEED_BASE}/${slug}.rss`
}

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

/** Fetch text with exponential backoff on 429/5xx. Returns "" on a 404. */
export async function textFetch(url: string): Promise<string> {
  const maxRetries = 6
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      headers: {
        "User-Agent": UA,
        Accept: "application/rss+xml,application/xml,text/xml,*/*",
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

export interface JobResult {
  id: string
  title: string
  company: string | null
  location: string | null
  date: string | null
  url: string
  remote: boolean
  visa: string | null
  category: string | null
  source: "weworkremotely"
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

function stripCdata(s: string): string {
  return s.replace(/<!\[CDATA\[/g, "").replace(/\]\]>/g, "").trim()
}

/** Convert an HTML fragment to readable text, preserving line breaks. */
export function htmlToText(html: string): string {
  const decodedOnce = decodeHtmlEntities(html) // RSS description is entity-escaped HTML
  const withBreaks = decodedOnce
    .replace(/<\s*br\s*\/?>/gi, "\n")
    .replace(/<\/(p|li|ul|ol|div|h\d)>/gi, "\n")
  return decodeHtmlEntities(withBreaks.replace(/<[^>]+>/g, " "))
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/ *\n */g, "\n")
    .trim()
}

function tag(xml: string, name: string): string | null {
  const m = xml.match(new RegExp(`<${name}[^>]*>([\\s\\S]*?)</${name}>`, "i"))
  return m ? decodeHtmlEntities(stripCdata(m[1])) : null
}

/** RFC-822 pubDate -> YYYY-MM-DD. */
export function isoDate(pubDate: string | null): string | null {
  if (!pubDate) return null
  const d = new Date(pubDate)
  return Number.isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10)
}

export function detectVisa(text: string): string | null {
  const hay = text.toLowerCase()
  if (/\b(relocation|relocate)\b/.test(hay)) return "relocation"
  if (/\b(visa|sponsor|sponsorship|work permit)\b/.test(hay)) return "sponsor"
  return null
}

export interface RawItem {
  title: string | null
  link: string | null
  guid: string | null
  pubDate: string | null
  region: string | null
  category: string | null
  description: string | null
}

/** Split the RSS into <item> blocks and pull each field. */
export function parseItems(xml: string): RawItem[] {
  const chunks = xml.split(/<item>/).slice(1).map((c) => c.split("</item>")[0])
  return chunks.map((c) => ({
    title: tag(c, "title"),
    link: tag(c, "link"),
    guid: tag(c, "guid"),
    pubDate: tag(c, "pubDate"),
    region: tag(c, "region"),
    category: tag(c, "category"),
    description: tag(c, "description"),
  }))
}

/** WWR item titles are usually "Company: Position". Split company off the front. */
function splitTitle(raw: string | null): { company: string | null; title: string } {
  if (!raw) return { company: null, title: "(untitled)" }
  const idx = raw.indexOf(": ")
  if (idx > 0 && idx < 60) {
    return { company: raw.slice(0, idx).trim(), title: raw.slice(idx + 2).trim() }
  }
  return { company: null, title: raw.trim() }
}

function slugFromUrl(url: string | null): string {
  if (!url) return ""
  const m = url.match(/remote-jobs\/([^/?#]+)/)
  return m ? m[1] : url.replace(/[/?#].*$/, "")
}

export function toResult(item: RawItem): JobResult {
  const { company, title } = splitTitle(item.title)
  const url = item.link || item.guid || ""
  const visaText = [item.title || "", item.description || "", item.region || ""].join(" ")
  return {
    id: slugFromUrl(url),
    title,
    company,
    location: item.region || null,
    date: isoDate(item.pubDate),
    url,
    remote: true, // every WWR listing is remote
    visa: detectVisa(visaText),
    category: item.category || null,
    source: "weworkremotely",
  }
}

/** Case-insensitive keyword match across title, region, category, description. */
export function matchesQuery(item: RawItem, query: string | undefined): boolean {
  if (!query) return true
  const hay = [item.title, item.region, item.category, item.description].join(" ").toLowerCase()
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((term) => hay.includes(term))
}
