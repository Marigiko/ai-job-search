import {
  API_URL,
  jsonFetch,
  extractJobs,
  toResult,
  writeError,
  type JobResult,
} from "../helpers.js"

export interface SearchOpts {
  query?: string
  location?: string
  visa?: boolean
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

function renderTable(rows: JobResult[]): string {
  if (rows.length === 0) return "No results."
  const line = (r: JobResult) => {
    const title = (r.title || "").slice(0, 38).padEnd(38)
    const company = (r.company || "—").slice(0, 20).padEnd(20)
    const loc = (r.location || "—").slice(0, 22).padEnd(22)
    return `${title} ${company} ${loc} ${(r.date || "—").padEnd(10)} ${r.visa || "—"}`
  }
  const header =
    "TITLE".padEnd(38) + " " + "COMPANY".padEnd(20) + " " + "LOCATION".padEnd(22) + " DATE       VISA"
  return [header, "-".repeat(header.length), ...rows.map(line)].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const limit = opts.limit !== undefined && opts.limit >= 0 ? opts.limit : 50
    const loc = opts.location?.toLowerCase()
    const params = new URLSearchParams()
    if (opts.query) params.set("search", opts.query)
    params.set("limit", String(Math.max(limit, 50)))
    const data = await jsonFetch(`${API_URL}?${params.toString()}`)
    const jobs = extractJobs(data)

    const collected: JobResult[] = []
    for (const raw of jobs) {
      const result = toResult(raw)
      if (!withinAge(result.date, opts.jobage)) continue
      if (loc && !(result.location || "").toLowerCase().includes(loc)) continue
      if (opts.visa && !result.visa) continue
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
              `${r.salaryText ? " · " + r.salaryText : ""}${r.visa ? " · " + r.visa : ""}\n  ${r.url}`,
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
