import {
  API_BASE,
  jsonFetch,
  htmlToText,
  toResult,
  resolveCompany,
  getSeniorityMap,
  seniorityLabel,
  writeError,
  type GobJob,
  type JobDetail,
} from "../helpers.js"

export interface DetailOpts {
  id: string // GetOnBoard job slug or public URL
  format: "json" | "plain"
}

/** Pull the slug from a public GetOnBoard job URL, else return input as-is. */
function slugOf(idOrUrl: string): string {
  const m = idOrUrl.match(/\/jobs\/([^/?#]+)/)
  if (m) return m[1]
  return idOrUrl.replace(/[/?#].*$/, "")
}

/** Candidate search queries derived from a slug, most-likely-to-match first.
 *  GetOnBoard's `query` is AND over terms, so a long query returns nothing; short
 *  distinctive queries (company/city near the slug tail, or the longest token)
 *  reliably surface the exact posting. We try candidates until the id matches. */
function queryCandidates(slug: string): string[] {
  const tokens = slug
    .replace(/-[a-z0-9]{3,6}$/i, "") // drop the trailing short hash
    .split("-")
    .filter((t) => t.length > 2)
  const longest = [...tokens].sort((a, b) => b.length - a.length)[0]
  const candidates = [
    tokens.slice(-2).join(" "), // company + city
    longest, // most distinctive single token (often the company)
    tokens.slice(-1).join(" "), // city
    tokens.slice(0, 3).join(" "), // role words
  ].filter(Boolean)
  return [...new Set(candidates)]
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  try {
    const slug = slugOf(opts.id)
    const seniorityMap = await getSeniorityMap()

    // The per-job endpoint requires auth (401); the search API returns the full
    // description inline, so we re-query with slug-derived keywords and match the id.
    // Try progressively broader candidate queries until the exact id shows up.
    let found: GobJob | null = null
    for (const query of queryCandidates(slug)) {
      const params = new URLSearchParams({ query, per_page: "50", page: "1" })
      const data = await jsonFetch(`${API_BASE}/search/jobs?${params.toString()}`)
      const jobs: GobJob[] = data && Array.isArray(data.data) ? data.data : []
      found = jobs.find((j) => j.id === slug) || null
      if (found) break
    }

    if (!found) {
      writeError(
        `job "${slug}" not found via search (it may be closed, or pass its full public URL)`,
        "NOT_FOUND",
      )
      return 1
    }

    const a = found.attributes || {}
    const companyName = await resolveCompany(a.company)
    const detail: JobDetail = {
      ...toResult(found, companyName, seniorityLabel(a.seniority, seniorityMap)),
      description: a.description ? htmlToText(a.description) : null,
    }

    if (opts.format === "plain") {
      const sal = detail.salaryMax ? ` · $${detail.salaryMin || "?"}-${detail.salaryMax}/mo USD` : ""
      process.stdout.write(
        `${detail.title}\n${detail.company || "—"} · ${detail.location || "—"} · ${detail.date || "—"}` +
          `${sal}${detail.seniority ? " · " + detail.seniority : ""}${detail.visa ? " · " + detail.visa : ""}\n` +
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
