import {
  API_URL,
  jsonFetch,
  htmlToText,
  toResult,
  writeError,
  type ArbeitnowRaw,
  type JobDetail,
} from "../helpers.js"

export interface DetailOpts {
  id: string // slug or full arbeitnow job URL
  format: "json" | "plain"
}

const MAX_PAGES = 5

/** Extract the slug from a full arbeitnow job URL, or return the input as-is. */
function normalizeSlug(idOrUrl: string): string {
  const m = idOrUrl.match(/\/jobs\/companies\/[^/]+\/([^/?#]+)/)
  if (m) return m[1]
  return idOrUrl.replace(/[/?#].*$/, "")
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  try {
    const slug = normalizeSlug(opts.id)
    // The API has no per-job endpoint; scan recent pages for the slug. The full
    // record (including the HTML description) is already present in the listing.
    let found: ArbeitnowRaw | null = null
    for (let p = 1; p <= MAX_PAGES; p++) {
      const data = await jsonFetch(`${API_URL}?page=${p}`)
      const jobs: ArbeitnowRaw[] = (data && Array.isArray(data.data) ? data.data : []) as ArbeitnowRaw[]
      if (jobs.length === 0) break
      found = jobs.find((j) => j.slug === slug) || null
      if (found) break
      if (!data?.links?.next) break
    }

    if (!found) {
      writeError(
        `job "${slug}" not found in the recent listing (it may have aged out of the API window)`,
        "NOT_FOUND",
      )
      return 1
    }

    const detail: JobDetail = {
      ...toResult(found),
      description: found.description ? htmlToText(found.description) : null,
    }

    if (opts.format === "plain") {
      process.stdout.write(
        `${detail.title}\n${detail.company || "—"} · ${detail.location || "—"} · ${detail.date || "—"}` +
          `${detail.remote ? " · remote" : ""}${detail.visa ? " · " + detail.visa : ""}\n` +
          `${detail.url}\n\n${detail.description || "(no description)"}\n`,
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
