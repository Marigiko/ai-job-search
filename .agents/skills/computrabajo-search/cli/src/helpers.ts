// Data source: Computrabajo public search pages (HTML, no auth). Country-scoped
// domains: ar (Argentina, default), mx, cl, pe, co, etc.
//   https://<country>.computrabajo.com/trabajo-de-<slug>?p=<page>
// We parse the offer cards with regex (shallow, stable markup). Zero runtime deps.
//
// ⚠️ Personal use only. This reads Computrabajo's public pages; automated access
// may be against their Terms of Service. Keep volume low and use it only for your
// own job search — not commercially or for bulk collection. Your own responsibility.

export function baseUrl(country: string): string {
  const c = (country || "ar").toLowerCase().replace(/[^a-z]/g, "")
  return `https://${c}.computrabajo.com`
}

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
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
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
  posted: string | null // raw relative text, e.g. "Hace 1 hora"
  source: "computrabajo"
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

function stripTags(html: string): string {
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()
}

function clean(html: string): string {
  return decodeHtmlEntities(stripTags(html))
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

/** Convert Computrabajo's relative Spanish "posted" text to an approximate ISO date. */
export function relativeToIso(posted: string | null): string | null {
  if (!posted) return null
  const s = posted.toLowerCase()
  const now = Date.now()
  const day = 86_400_000
  if (/hoy|hora|minuto|reci[eé]n/.test(s)) return new Date(now).toISOString().slice(0, 10)
  if (/ayer/.test(s)) return new Date(now - day).toISOString().slice(0, 10)
  const m = s.match(/hace\s+(\d+)\s+(d[ií]a|semana|mes)/)
  if (m) {
    const n = parseInt(m[1], 10)
    const unit = m[2].startsWith("sem") ? 7 * day : m[2].startsWith("mes") ? 30 * day : day
    return new Date(now - n * unit).toISOString().slice(0, 10)
  }
  return null
}

function detectRemote(modality: string | null): boolean {
  return !!modality && /remoto|remote|teletrabajo|home ?office/i.test(modality)
}

export function detectVisa(text: string): string | null {
  const hay = text.toLowerCase()
  if (/relocaci|relocation|relocate|mudanza/.test(hay)) return "relocation"
  if (/\b(visa|sponsor|sponsorship|patrocinio)\b/.test(hay)) return "sponsor"
  return null
}

/** Parse the search result cards. */
export function parseCards(html: string, base: string): JobResult[] {
  const results: JobResult[] = []
  const chunks = html.split(/<article class="box_offer/).slice(1)
  for (const chunk of chunks) {
    const idMatch = chunk.match(/data-id='([^']+)'/) || chunk.match(/id="([0-9A-F]{16,})"/)
    const id = idMatch ? idMatch[1] : ""

    const linkMatch = chunk.match(/class="js-o-link[^"]*"[^>]*href="([^"#]+)[^"]*"[^>]*>([\s\S]*?)<\/a>/i)
    if (!linkMatch) continue
    const href = decodeHtmlEntities(linkMatch[1])
    const url = href.startsWith("http") ? href : base + href
    const title = clean(linkMatch[2])
    if (!title) continue

    const companyMatch = chunk.match(/offer-grid-article-company-url>\s*([\s\S]*?)<\/a>/i)
    const company = companyMatch ? clean(companyMatch[1]) || null : null

    const locMatch = chunk.match(/<p class="fs16 fc_base mt5">\s*<span class="mr10">([\s\S]*?)<\/span>/i)
    const location = locMatch ? clean(locMatch[1]) || null : null

    const modalityMatch = chunk.match(/i_home_office"><\/span>\s*([\s\S]*?)<\/span>/i)
    const modality = modalityMatch ? clean(modalityMatch[1]) || null : null

    const dateMatch = chunk.match(/class="fs13 fc_aux[^"]*">\s*([\s\S]*?)<\/p>/i)
    const posted = dateMatch ? clean(dateMatch[1]) || null : null

    results.push({
      id: id || url,
      title,
      company,
      location,
      date: relativeToIso(posted),
      url,
      remote: detectRemote(modality),
      visa: detectVisa(`${title} ${location ?? ""} ${modality ?? ""}`),
      posted,
      source: "computrabajo",
    })
  }
  return results
}

/** Best-effort title/company/location from an offer detail page header. */
export function parseOfferHeader(html: string): { title: string | null; company: string | null; location: string | null } {
  const h1 = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)
  let title = h1 ? clean(h1[1]) || null : null
  if (!title) {
    const og = html.match(/<meta property="og:title" content="([^"]*)"/i)
    title = og ? decodeHtmlEntities(og[1]).replace(/^Trabajo de\s+/i, "") || null : null
  }
  const companyMatch = html.match(/offer-company-name[^>]*>([\s\S]*?)<\/a>/i) ||
    html.match(/class="fc_base[^"]*"[^>]*href="\/[^"]*"[^>]*offer[^>]*>([\s\S]*?)<\/a>/i)
  const company = companyMatch ? clean(companyMatch[1]) || null : null
  return { title, company, location: null }
}

/** Parse the offer detail page: the block under "Descripción de la oferta". */
export function parseDetailDescription(html: string): string | null {
  const i = html.search(/Descripci[oó]n de la oferta<\/h3>/i)
  if (i === -1) {
    const og = html.match(/<meta property="og:description" content="([^"]*)"/i)
    return og ? decodeHtmlEntities(og[1]) : null
  }
  // Capture from the header to the next <h3> (next section) or a bounded window.
  const rest = html.slice(i)
  const end = rest.slice(20).search(/<h3\b/i)
  const block = end === -1 ? rest.slice(0, 6000) : rest.slice(0, end + 20)
  const text = htmlToText(block.replace(/^[^>]*>/, ""))
  return text || null
}
