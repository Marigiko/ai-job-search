export interface SearchOptions {
  role?: string
  remote?: boolean
  batch?: string
  maxResults?: string
  engine?: string
}

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

export function writeOutput(data: unknown): void {
  process.stdout.write(JSON.stringify(data, null, 2) + "\n")
}

const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

const YC_JOB_RE = /https?:\/\/www\.workatastartup\.com\/jobs\/[^\s"'<>]+/g
const YC_COMPANY_RE = /https?:\/\/www\.workatastartup\.com\/companies\/[^\s"'<>]+/g

function buildQuery(opts: SearchOptions): string {
  const role = opts.role || "software engineer"
  const parts = [`site:workatastartup.com/jobs`, `"${role}"`]
  if (opts.remote) parts.push("remote")
  if (opts.batch) parts.push(`"${opts.batch}"")
  return parts.join(" ")
}

async function searchDuckDuckGo(query: string, maxResults: number): Promise<string[]> {
  const encoded = encodeURIComponent(query)
  const url = `https://html.duckduckgo.com/html/?q=${encoded}`
  try {
    const resp = await fetch(url, {
      headers: { "User-Agent": UA, Accept: "text/html" },
    })
    if (!resp.ok) return []
    const html = await resp.text()
    const links = new Set<string>()
    const jobMatches = html.match(YC_JOB_RE) || []
    const companyMatches = html.match(YC_COMPANY_RE) || []
    for (const m of [...jobMatches, ...companyMatches]) {
      links.add(m)
    }
    // Also extract from redirect URLs
    const redirectMatches = html.match(/uddg=([^&]+)/g) || []
    for (const rm of redirectMatches) {
      const decoded = decodeURIComponent(rm.replace("uddg=", ""))
      if (decoded.includes("workatastartup.com")) {
        links.add(decoded)
      }
    }
    return [...links].slice(0, maxResults)
  } catch {
    return []
  }
}

async function searchBing(query: string, maxResults: number): Promise<string[]> {
  const encoded = encodeURIComponent(query)
  const url = `https://www.bing.com/search?q=${encoded}&count=${maxResults * 2}`
  try {
    const resp = await fetch(url, {
      headers: { "User-Agent": UA, Accept: "text/html" },
    })
    if (!resp.ok) return []
    const html = await resp.text()
    const links = new Set<string>()
    const jobMatches = html.match(YC_JOB_RE) || []
    const companyMatches = html.match(YC_COMPANY_RE) || []
    for (const m of [...jobMatches, ...companyMatches]) {
      links.add(m)
    }
    return [...links].slice(0, maxResults)
  } catch {
    return []
  }
}

function parseJobSlug(url: string): { title: string; company: string } {
  const slug = url.split("/").pop() || ""
  const decoded = slug.replace(/-/g, " ")
  // workatastastup.com/jobs/<id>-<role>-at-<company>
  const atMatch = decoded.match(/(.+?)\s+at\s+(.+)/i)
  if (atMatch) {
    return { title: atMatch[1].trim(), company: atMatch[2].trim() }
  }
  return { title: decoded, company: "" }
}

export async function runSearch(opts: SearchOptions): Promise<number> {
  const maxResults = parseInt(opts.maxResults || "10", 10)
  const engine = opts.engine === "google" ? "google" : "bing"
  const query = buildQuery(opts)

  let urls: string[] = []
  if (engine === "google") {
    // DuckDuckGo is the free alternative to Google
    urls = await searchDuckDuckGo(query, maxResults)
  }
  if (urls.length === 0) {
    urls = await searchBing(query, maxResults)
  }
  if (urls.length === 0) {
    // Fallback to DuckDuckGo if Bing failed
    urls = await searchDuckDuckGo(query, maxResults)
  }

  const results = urls.map((url) => {
    const { title, company } = parseJobSlug(url)
    return {
      id: url.split("/").pop() || url,
      title: title || "YC Startup Job",
      company: company || "",
      location: null as string | null,
      date: null as string | null,
      url: url.split("?")[0],
      applyEmail: null as string | null,
      emails: [] as string[],
      author: null as string | null,
      text: null as string | null,
      source: "yc-startup-job",
    }
  })

  writeOutput({ meta: { count: results.length }, results })
  return 0
}
