import { baseUrl, htmlFetch, parseCards, writeError, type JobResult } from "../helpers.js"

export interface SearchOpts {
  query?: string
  country: string
  location?: string
  visa?: boolean
  page: number
  limit?: number
  format: "json" | "table" | "plain"
}

const MAX_PAGES = 5

function slugify(q: string): string {
  return q
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
}

function buildUrl(base: string, opts: SearchOpts, page: number): string {
  const slug = opts.query ? slugify(opts.query) : "trabajo"
  const path = `/trabajo-de-${slug}`
  const qs = page > 1 ? `?p=${page}` : ""
  return `${base}${path}${qs}`
}

function renderTable(rows: JobResult[]): string {
  if (rows.length === 0) return "No results."
  const line = (r: JobResult) => {
    const title = (r.title || "").slice(0, 38).padEnd(38)
    const company = (r.company || "—").slice(0, 22).padEnd(22)
    const loc = (r.location || "—").slice(0, 24).padEnd(24)
    const flags = [r.remote ? "remote" : "", r.visa || ""].filter(Boolean).join("/") || "—"
    return `${title} ${company} ${loc} ${(r.posted || "—").slice(0, 12).padEnd(12)} ${flags}`
  }
  const header =
    "TITLE".padEnd(38) + " " + "COMPANY".padEnd(22) + " " + "LOCATION".padEnd(24) + " POSTED       FLAGS"
  return [header, "-".repeat(header.length), ...rows.map(line)].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const base = baseUrl(opts.country)
    const limit = opts.limit !== undefined && opts.limit >= 0 ? opts.limit : 50
    const loc = opts.location?.toLowerCase()
    const collected: JobResult[] = []
    const seen = new Set<string>()

    for (let p = opts.page; p < opts.page + MAX_PAGES; p++) {
      const html = await htmlFetch(buildUrl(base, opts, p))
      if (!html) break
      const cards = parseCards(html, base)
      if (cards.length === 0) break
      for (const r of cards) {
        if (seen.has(r.id)) continue
        seen.add(r.id)
        if (loc && !(r.location || "").toLowerCase().includes(loc)) continue
        if (opts.visa && !r.visa) continue
        collected.push(r)
        if (collected.length >= limit) break
      }
      if (collected.length >= limit) break
    }

    if (opts.format === "table") {
      process.stdout.write(renderTable(collected) + "\n")
    } else if (opts.format === "plain") {
      process.stdout.write(
        collected
          .map(
            (r) =>
              `${r.title}\n  ${r.company || "—"} · ${r.location || "—"} · ${r.posted || "—"}` +
              `${r.remote ? " · remote" : ""}${r.visa ? " · " + r.visa : ""}\n  ${r.url}`,
          )
          .join("\n\n") + "\n",
      )
    } else {
      process.stdout.write(
        JSON.stringify({ meta: { count: collected.length, page: opts.page, country: opts.country }, results: collected }, null, 2) + "\n",
      )
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "SEARCH_FAILED")
    return 1
  }
}
