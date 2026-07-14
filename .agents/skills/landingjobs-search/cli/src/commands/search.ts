import {
  API_URL,
  jsonFetch,
  matchesQuery,
  toResult,
  writeError,
  type LjRaw,
  type JobResult,
} from "../helpers.js"

export interface SearchOpts {
  query?: string
  location?: string
  remote?: boolean
  visa?: boolean
  minSalary?: number // annual gross floor, in the posting's currency
  jobage: number
  page: number
  limit?: number
  format: "json" | "table" | "plain"
}

const MAX_PAGES = 5

function withinAge(published: string | undefined, days: number): boolean {
  if (!days || days >= 9999) return true
  if (!published) return true
  const t = new Date(published).getTime()
  if (Number.isNaN(t)) return true
  return (Date.now() - t) / 86_400_000 <= days
}

function fmtSalary(r: JobResult): string {
  const c = r.currency || ""
  if (r.salaryLow && r.salaryHigh) return `${Math.round(r.salaryLow / 1000)}-${Math.round(r.salaryHigh / 1000)}k ${c}`
  if (r.salaryHigh) return `<=${Math.round(r.salaryHigh / 1000)}k ${c}`
  return "—"
}

function renderTable(rows: JobResult[]): string {
  if (rows.length === 0) return "No results."
  const line = (r: JobResult) => {
    const title = (r.title || "").slice(0, 36).padEnd(36)
    const company = (r.company || "—").slice(0, 18).padEnd(18)
    const loc = (r.location || "—").slice(0, 18).padEnd(18)
    const sal = fmtSalary(r).padEnd(13)
    const flags = [r.remote ? "remote" : "", r.visa || ""].filter(Boolean).join("/") || "—"
    return `${title} ${company} ${loc} ${sal} ${flags}`
  }
  const header =
    "TITLE".padEnd(36) + " " + "COMPANY".padEnd(18) + " " + "LOCATION".padEnd(18) + " " + "SALARY(/yr)".padEnd(13) + " FLAGS"
  return [header, "-".repeat(header.length), ...rows.map(line)].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const limit = opts.limit !== undefined && opts.limit >= 0 ? opts.limit : 50
    const loc = opts.location?.toLowerCase()
    const collected: JobResult[] = []

    for (let p = opts.page; p < opts.page + MAX_PAGES; p++) {
      const data = await jsonFetch(`${API_URL}?page=${p}`)
      const jobs: LjRaw[] = Array.isArray(data) ? data : []
      if (jobs.length === 0) break

      for (const raw of jobs) {
        if (!matchesQuery(raw, opts.query)) continue
        if (opts.remote && !raw.remote) continue
        if (!withinAge(raw.published_at, opts.jobage)) continue
        const result = toResult(raw)
        if (loc && !(result.location || "").toLowerCase().includes(loc)) continue
        if (opts.visa && !result.visa) continue
        if (opts.minSalary && result.salaryHigh !== null && result.salaryHigh < opts.minSalary) continue
        collected.push(result)
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
              `${r.title}\n  ${r.company || "—"} · ${r.location || "—"} · ${r.date || "—"}` +
              `${r.salaryHigh ? " · " + fmtSalary(r) : ""}${r.remote ? " · remote" : ""}${r.visa ? " · " + r.visa : ""}\n  ${r.url}`,
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
