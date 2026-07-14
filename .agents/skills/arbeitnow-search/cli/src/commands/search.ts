import {
  API_URL,
  jsonFetch,
  matchesQuery,
  toResult,
  writeError,
  type ArbeitnowRaw,
  type JobResult,
} from "../helpers.js"

export interface SearchOpts {
  query?: string
  location?: string
  remote?: boolean
  visa?: boolean
  jobage: number
  page: number
  limit?: number
  format: "json" | "table" | "plain"
}

const MAX_PAGES = 5 // safety cap: at 100 jobs/page this scans up to ~500 recent jobs

function withinAge(raw: ArbeitnowRaw, days: number): boolean {
  if (!days || days >= 9999) return true
  if (!raw.created_at) return true
  const ageDays = (Date.now() / 1000 - raw.created_at) / 86400
  return ageDays <= days
}

function renderTable(rows: JobResult[]): string {
  if (rows.length === 0) return "No results."
  const line = (r: JobResult) => {
    const title = (r.title || "").slice(0, 40).padEnd(40)
    const company = (r.company || "—").slice(0, 22).padEnd(22)
    const loc = (r.location || "—").slice(0, 18).padEnd(18)
    const flags = [r.remote ? "remote" : "", r.visa || ""].filter(Boolean).join("/") || "—"
    return `${title} ${company} ${loc} ${(r.date || "—").padEnd(10)} ${flags}`
  }
  const header =
    "TITLE".padEnd(40) + " " + "COMPANY".padEnd(22) + " " + "LOCATION".padEnd(18) + " DATE       FLAGS"
  return [header, "-".repeat(header.length), ...rows.map(line)].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const limit = opts.limit !== undefined && opts.limit >= 0 ? opts.limit : 50
    const loc = opts.location?.toLowerCase()
    const collected: JobResult[] = []

    // The API returns latest jobs per page with no keyword search, so we page
    // forward (starting at opts.page) filtering client-side until we have enough.
    for (let p = opts.page; p < opts.page + MAX_PAGES; p++) {
      const data = await jsonFetch(`${API_URL}?page=${p}`)
      const jobs: ArbeitnowRaw[] = (data && Array.isArray(data.data) ? data.data : []) as ArbeitnowRaw[]
      if (jobs.length === 0) break

      for (const raw of jobs) {
        if (!matchesQuery(raw, opts.query)) continue
        if (opts.remote && !raw.remote) continue
        if (!withinAge(raw, opts.jobage)) continue
        if (loc && !(raw.location || "").toLowerCase().includes(loc)) continue
        const result = toResult(raw)
        if (opts.visa && !result.visa) continue
        collected.push(result)
        if (collected.length >= limit) break
      }
      if (collected.length >= limit) break
      if (!data?.links?.next) break
    }

    if (opts.format === "table") {
      process.stdout.write(renderTable(collected) + "\n")
    } else if (opts.format === "plain") {
      process.stdout.write(
        collected
          .map(
            (r) =>
              `${r.title}\n  ${r.company || "—"} · ${r.location || "—"} · ${r.date || "—"}` +
              `${r.remote ? " · remote" : ""}${r.visa ? " · " + r.visa : ""}\n  ${r.url}`,
          )
          .join("\n\n") + "\n",
      )
    } else {
      process.stdout.write(
        JSON.stringify(
          { meta: { count: collected.length, page: opts.page }, results: collected },
          null,
          2,
        ) + "\n",
      )
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "SEARCH_FAILED")
    return 1
  }
}
