import {
  API_URL,
  jsonFetch,
  extractJobs,
  toResult,
  monthlyEstimate,
  writeError,
  type JobResult,
} from "../helpers.js"

export interface SearchOpts {
  query?: string
  geo?: string
  visa?: boolean
  minSalaryMonthly?: number // monthly-USD floor (compared to a rough estimate)
  jobage: number
  limit?: number
  format: "json" | "table" | "plain"
}

function withinAge(date: string | null, days: number): boolean {
  if (!days || days >= 9999 || !date) return true
  const t = new Date(date).getTime()
  if (Number.isNaN(t)) return true
  return (Date.now() - t) / 86_400_000 <= days
}

function fmtSalary(r: JobResult): string {
  if (r.salaryMin && r.salaryMax)
    return `${Math.round(r.salaryMin / 1000)}-${Math.round(r.salaryMax / 1000)}k ${r.salaryCurrency || ""}`
  if (r.salaryMax) return `<=${Math.round(r.salaryMax / 1000)}k ${r.salaryCurrency || ""}`
  return "—"
}

function renderTable(rows: JobResult[]): string {
  if (rows.length === 0) return "No results."
  const line = (r: JobResult) => {
    const title = (r.title || "").slice(0, 36).padEnd(36)
    const company = (r.company || "—").slice(0, 20).padEnd(20)
    const geo = (r.location || "—").slice(0, 16).padEnd(16)
    const sal = fmtSalary(r).padEnd(15)
    return `${title} ${company} ${geo} ${sal} ${r.visa || "—"}`
  }
  const header =
    "TITLE".padEnd(36) + " " + "COMPANY".padEnd(20) + " " + "GEO".padEnd(16) + " " + "SALARY(/yr)".padEnd(15) + " VISA"
  return [header, "-".repeat(header.length), ...rows.map(line)].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const limit = opts.limit !== undefined && opts.limit >= 0 ? opts.limit : 50
    const params = new URLSearchParams()
    params.set("count", String(Math.min(Math.max(limit, 1), 50)))
    if (opts.query) params.set("tag", opts.query)
    if (opts.geo) params.set("geo", opts.geo)
    const data = await jsonFetch(`${API_URL}?${params.toString()}`)
    const jobs = extractJobs(data)

    const collected: JobResult[] = []
    for (const raw of jobs) {
      const result = toResult(raw)
      if (!withinAge(result.date, opts.jobage)) continue
      if (opts.visa && !result.visa) continue
      if (opts.minSalaryMonthly) {
        const est = monthlyEstimate(result)
        if (est !== null && est < opts.minSalaryMonthly) continue
      }
      collected.push(result)
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
              `${r.salaryMax ? " · " + fmtSalary(r) + "/" + (r.salaryPeriod || "yr") : ""}` +
              `${r.level ? " · " + r.level : ""}${r.visa ? " · " + r.visa : ""}\n  ${r.url}`,
          )
          .join("\n\n") + "\n",
      )
    } else {
      process.stdout.write(
        JSON.stringify({ meta: { count: collected.length, page: 1 }, results: collected }, null, 2) + "\n",
      )
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "SEARCH_FAILED")
    return 1
  }
}
