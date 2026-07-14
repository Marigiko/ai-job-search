import {
  API_URL,
  jsonFetch,
  isJob,
  matchesQuery,
  toResult,
  writeError,
  type RemoteOkRaw,
  type JobResult,
} from "../helpers.js"

export interface SearchOpts {
  query?: string
  location?: string
  visa?: boolean
  minSalary?: number // annual USD floor
  jobage: number
  limit?: number
  format: "json" | "table" | "plain"
}

function withinAge(raw: RemoteOkRaw, days: number): boolean {
  if (!days || days >= 9999) return true
  if (!raw.epoch) return true
  const ageDays = (Date.now() / 1000 - raw.epoch) / 86400
  return ageDays <= days
}

function fmtSalary(r: JobResult): string {
  if (r.salaryMin && r.salaryMax) return `$${Math.round(r.salaryMin / 1000)}-${Math.round(r.salaryMax / 1000)}k`
  if (r.salaryMax) return `<=$${Math.round(r.salaryMax / 1000)}k`
  return "—"
}

function renderTable(rows: JobResult[]): string {
  if (rows.length === 0) return "No results."
  const line = (r: JobResult) => {
    const title = (r.title || "").slice(0, 38).padEnd(38)
    const company = (r.company || "—").slice(0, 22).padEnd(22)
    const sal = fmtSalary(r).padEnd(12)
    const flags = r.visa || "—"
    return `${title} ${company} ${sal} ${(r.date || "—").padEnd(10)} ${flags}`
  }
  const header =
    "TITLE".padEnd(38) + " " + "COMPANY".padEnd(22) + " " + "SALARY(USD/y)".padEnd(12) + " DATE       VISA"
  return [header, "-".repeat(header.length), ...rows.map(line)].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const limit = opts.limit !== undefined && opts.limit >= 0 ? opts.limit : 50
    const loc = opts.location?.toLowerCase()
    const data = await jsonFetch(API_URL)
    const jobs: RemoteOkRaw[] = Array.isArray(data) ? data.filter(isJob) : []

    const collected: JobResult[] = []
    for (const raw of jobs) {
      if (!matchesQuery(raw, opts.query)) continue
      if (!withinAge(raw, opts.jobage)) continue
      if (loc && !(raw.location || "").toLowerCase().includes(loc)) continue
      const result = toResult(raw)
      if (opts.visa && !result.visa) continue
      // Salary floor: exclude only jobs whose KNOWN max is below the floor.
      // Unknown-salary jobs pass through (never hidden), to be confirmed later.
      if (opts.minSalary && result.salaryMax !== null && result.salaryMax < opts.minSalary) continue
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
              `${r.salaryMax ? " · " + fmtSalary(r) + " USD/yr" : ""}${r.visa ? " · " + r.visa : ""}\n  ${r.url}`,
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
