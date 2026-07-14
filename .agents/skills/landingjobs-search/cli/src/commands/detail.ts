import {
  API_URL,
  jsonFetch,
  composeDescription,
  toResult,
  writeError,
  type LjRaw,
  type JobDetail,
} from "../helpers.js"

export interface DetailOpts {
  id: string // Landing.jobs numeric id or full job URL
  format: "json" | "plain"
}

const MAX_PAGES = 5

function idOf(idOrUrl: string): string {
  // Full URLs don't contain the numeric id; callers should pass the id from
  // search. If a URL is given, we match on it instead.
  return idOrUrl.trim()
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  try {
    const key = idOf(opts.id)
    const isUrl = /^https?:\/\//.test(key)
    let found: LjRaw | null = null

    for (let p = 1; p <= MAX_PAGES && !found; p++) {
      const data = await jsonFetch(`${API_URL}?page=${p}`)
      const jobs: LjRaw[] = Array.isArray(data) ? data : []
      if (jobs.length === 0) break
      found = jobs.find((j) => (isUrl ? j.url === key : String(j.id) === key)) || null
    }

    if (!found) {
      writeError(
        `job "${key}" not found in the current Landing.jobs feed (it may have expired)`,
        "NOT_FOUND",
      )
      return 1
    }

    const detail: JobDetail = {
      ...toResult(found),
      description: composeDescription(found),
    }

    if (opts.format === "plain") {
      const sal = detail.salaryHigh
        ? ` · ${detail.salaryLow || "?"}-${detail.salaryHigh} ${detail.currency || ""}/yr`
        : ""
      process.stdout.write(
        `${detail.title}\n${detail.company || "—"} · ${detail.location || "—"} · ${detail.date || "—"}` +
          `${sal}${detail.remote ? " · remote" : ""}${detail.visa ? " · " + detail.visa : ""}\n${detail.url}\n\n` +
          `${detail.description || "(no description)"}\n`,
      )
    } else {
      process.stdout.write(JSON.stringify(detail, null, 2) + "\n")
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "DETAIL_FAILED")
    return 1
  }
}
