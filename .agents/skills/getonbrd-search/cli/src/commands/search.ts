import {
  API_BASE,
  jsonFetch,
  toResult,
  resolveCompany,
  getSeniorityMap,
  seniorityLabel,
  writeError,
  type GobJob,
  type JobResult,
} from "../helpers.js"

export interface SearchOpts {
  query?: string
  remote?: boolean
  visa?: boolean
  minSalary?: number // monthly USD floor
  jobage: number
  page: number
  perPage: number
  limit?: number
  format: "json" | "table" | "plain"
}

const MAX_PAGES = 5

function withinAge(publishedAt: number | undefined, days: number): boolean {
  if (!days || days >= 9999) return true
  if (!publishedAt) return true
  return (Date.now() / 1000 - publishedAt) / 86400 <= days
}

function fmtSalary(r: JobResult): string {
  if (r.salaryMin && r.salaryMax) return `$${r.salaryMin}-${r.salaryMax}/mo`
  if (r.salaryMax) return `<=$${r.salaryMax}/mo`
  return "—"
}

function renderTable(rows: JobResult[]): string {
  if (rows.length === 0) return "No results."
  const line = (r: JobResult) => {
    const title = (r.title || "").slice(0, 36).padEnd(36)
    const company = (r.company || "—").slice(0, 20).padEnd(20)
    const sal = fmtSalary(r).padEnd(14)
    const flags = [r.remote ? "remote" : "", r.visa || ""].filter(Boolean).join("/") || "—"
    return `${title} ${company} ${sal} ${(r.date || "—").padEnd(10)} ${flags}`
  }
  const header =
    "TITLE".padEnd(36) + " " + "COMPANY".padEnd(20) + " " + "SALARY(USD/mo)".padEnd(14) + " DATE       FLAGS"
  return [header, "-".repeat(header.length), ...rows.map(line)].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const limit = opts.limit !== undefined && opts.limit >= 0 ? opts.limit : 50
    const seniorityMap = await getSeniorityMap()
    const raw: GobJob[] = []

    for (let p = opts.page; p < opts.page + MAX_PAGES && raw.length < limit * 2; p++) {
      const params = new URLSearchParams()
      if (opts.query) params.set("query", opts.query)
      if (opts.remote) params.set("remote", "true")
      params.set("per_page", String(opts.perPage))
      params.set("page", String(p))
      const data = await jsonFetch(`${API_BASE}/search/jobs?${params.toString()}`)
      const jobs: GobJob[] = data && Array.isArray(data.data) ? data.data : []
      if (jobs.length === 0) break
      raw.push(...jobs)
      const totalPages = data?.meta?.total_pages
      if (totalPages && p >= totalPages) break
    }

    // Resolve labels and apply client-side filters (visa, salary, age).
    const collected: JobResult[] = []
    for (const job of raw) {
      const a = job.attributes || {}
      if (!withinAge(a.published_at, opts.jobage)) continue
      const companyName = await resolveCompany(a.company)
      const result = toResult(job, companyName, seniorityLabel(a.seniority, seniorityMap))
      if (opts.visa && !result.visa) continue
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
              `${r.salaryMax ? " · " + fmtSalary(r) + " USD" : ""}${r.remote ? " · remote" : ""}` +
              `${r.visa ? " · " + r.visa : ""}\n  ${r.url}`,
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
