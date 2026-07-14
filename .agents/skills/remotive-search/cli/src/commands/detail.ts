import {
  API_URL,
  jsonFetch,
  extractJobs,
  htmlToText,
  toResult,
  writeError,
  type RemotiveRaw,
  type JobDetail,
} from "../helpers.js"

export interface DetailOpts {
  id: string // Remotive numeric id or full job URL
  format: "json" | "plain"
}

function idOf(idOrUrl: string): string {
  const m = idOrUrl.match(/-(\d+)(?:\/|$)/) || idOrUrl.match(/(\d{4,})/)
  return m ? m[1] : idOrUrl.trim()
}

/** Keywords from a Remotive job-URL slug, to drive the search-based lookup. */
function keywordsFromUrl(idOrUrl: string): string {
  const m = idOrUrl.match(/remote-jobs\/[^/]+\/([^/?#]+)/)
  if (!m) return ""
  return m[1]
    .replace(/-\d+$/, "")
    .split("-")
    .filter((t) => t.length > 2)
    .slice(0, 4)
    .join(" ")
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  try {
    const id = idOf(opts.id)
    const query = keywordsFromUrl(opts.id)
    const params = new URLSearchParams({ limit: "100" })
    if (query) params.set("search", query)
    const data = await jsonFetch(`${API_URL}?${params.toString()}`)
    const jobs: RemotiveRaw[] = extractJobs(data)
    const found = jobs.find((j) => String(j.id) === id) || null

    if (!found) {
      writeError(`job "${id}" not found in the current Remotive feed`, "NOT_FOUND")
      return 1
    }

    const detail: JobDetail = {
      ...toResult(found),
      description: found.description ? htmlToText(found.description) : null,
    }

    if (opts.format === "plain") {
      process.stdout.write(
        `${detail.title}\n${detail.company || "—"} · ${detail.location || "—"} · ${detail.date || "—"}` +
          `${detail.salaryText ? " · " + detail.salaryText : ""}${detail.visa ? " · " + detail.visa : ""}\n${detail.url}\n\n` +
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
