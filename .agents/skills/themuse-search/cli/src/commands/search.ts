import {
  API_BASE,
  jsonFetch,
  matchesQuery,
  toResult,
  writeError,
  type MuseRaw,
  type JobResult,
} from "../helpers.js"

export interface SearchOpts {
  query?: string
  location?: string
  category?: string
  level?: string
  visa?: boolean
  page: number
  limit?: number
  format: "json" | "table" | "plain"
}

const MAX_PAGES = 5

function renderTable(rows: JobResult[]): string {
  if (rows.length === 0) return "No results."
  const line = (r: JobResult) => {
    const title = (r.title || "").slice(0, 36).padEnd(36)
    const company = (r.company || "—").slice(0, 20).padEnd(20)
    const loc = (r.location || "—").slice(0, 24).padEnd(24)
    const flags = [r.remote ? "remote" : "", r.visa || ""].filter(Boolean).join("/") || "—"
    return `${title} ${company} ${loc} ${(r.date || "—").padEnd(10)} ${flags}`
  }
  const header =
    "TITLE".padEnd(36) + " " + "COMPANY".padEnd(20) + " " + "LOCATION".padEnd(24) + " DATE       FLAGS"
  return [header, "-".repeat(header.length), ...rows.map(line)].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const limit = opts.limit !== undefined && opts.limit >= 0 ? opts.limit : 50
    const collected: JobResult[] = []

    for (let p = opts.page; p < opts.page + MAX_PAGES; p++) {
      const params = new URLSearchParams({ page: String(p) })
      if (opts.location) params.set("location", opts.location)
      if (opts.category) params.set("category", opts.category)
      if (opts.level) params.set("level", opts.level)
      const data = await jsonFetch(`${API_BASE}?${params.toString()}`)
      const jobs: MuseRaw[] = data && Array.isArray(data.results) ? data.results : []
      if (jobs.length === 0) break

      for (const raw of jobs) {
        if (!matchesQuery(raw, opts.query)) continue
        const result = toResult(raw)
        if (opts.visa && !result.visa) continue
        collected.push(result)
        if (collected.length >= limit) break
      }
      if (collected.length >= limit) break
      if (data.page_count && p >= data.page_count) break
    }

    if (opts.format === "table") {
      process.stdout.write(renderTable(collected) + "\n")
    } else if (opts.format === "plain") {
      process.stdout.write(
        collected
          .map(
            (r) =>
              `${r.title}\n  ${r.company || "—"} · ${r.location || "—"} · ${r.date || "—"}` +
              `${r.level ? " · " + r.level : ""}${r.remote ? " · remote" : ""}${r.visa ? " · " + r.visa : ""}\n  ${r.url}`,
          )
          .join("\n\n") + "\n",
      )
    } else {
      process.stdout.write(
        JSON.stringify({ meta: { count: collected.length, page: opts.page }, results: collected }, null, 2) + "\n",
      )
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "SEARCH_FAILED")
    return 1
  }
}
