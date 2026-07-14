import {
  API_URL,
  jsonFetch,
  extractJobs,
  htmlToText,
  toResult,
  writeError,
  type JobicyRaw,
  type JobDetail,
} from "../helpers.js"

export interface DetailOpts {
  id: string // Jobicy numeric id or full job URL
  format: "json" | "plain"
}

function idOf(idOrUrl: string): string {
  const m = idOrUrl.match(/\/jobs\/(\d+)/) || idOrUrl.match(/(\d{3,})/)
  return m ? m[1] : idOrUrl.trim()
}

/** Keywords from a Jobicy job-URL slug, to drive the tag-based lookup. */
function keywordsFromUrl(idOrUrl: string): string {
  const m = idOrUrl.match(/\/jobs\/\d+-([^/?#]+)/)
  if (!m) return ""
  return m[1]
    .split("-")
    .filter((t) => t.length > 2)
    .slice(0, 3)
    .join(" ")
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  try {
    const id = idOf(opts.id)
    const tag = keywordsFromUrl(opts.id)
    const params = new URLSearchParams({ count: "50" })
    if (tag) params.set("tag", tag)
    const data = await jsonFetch(`${API_URL}?${params.toString()}`)
    const jobs: JobicyRaw[] = extractJobs(data)
    const found = jobs.find((j) => String(j.id) === id) || null

    if (!found) {
      writeError(`job "${id}" not found in the current Jobicy feed`, "NOT_FOUND")
      return 1
    }

    const detail: JobDetail = {
      ...toResult(found),
      description: found.jobDescription ? htmlToText(found.jobDescription) : null,
    }

    if (opts.format === "plain") {
      const sal = detail.salaryMax
        ? ` · ${detail.salaryMin || "?"}-${detail.salaryMax} ${detail.salaryCurrency || ""}/${detail.salaryPeriod || "yr"}`
        : ""
      process.stdout.write(
        `${detail.title}\n${detail.company || "—"} · ${detail.location || "—"} · ${detail.date || "—"}` +
          `${sal}${detail.level ? " · " + detail.level : ""}${detail.visa ? " · " + detail.visa : ""}\n${detail.url}\n\n` +
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
