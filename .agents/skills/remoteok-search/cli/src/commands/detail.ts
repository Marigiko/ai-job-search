import {
  API_URL,
  jsonFetch,
  isJob,
  htmlToText,
  toResult,
  writeError,
  type RemoteOkRaw,
  type JobDetail,
} from "../helpers.js"

export interface DetailOpts {
  id: string // RemoteOK numeric id, slug, or full job URL
  format: "json" | "plain"
}

/** Pull an id or slug out of a full RemoteOK job URL, else return input as-is. */
function normalize(idOrUrl: string): string {
  const m = idOrUrl.match(/remote-jobs\/([^/?#]+)/)
  if (m) return m[1]
  return idOrUrl.replace(/[/?#].*$/, "")
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  try {
    const key = normalize(opts.id)
    const data = await jsonFetch(API_URL)
    const jobs: RemoteOkRaw[] = Array.isArray(data) ? data.filter(isJob) : []
    // Match by id, slug, or slug-suffix (the URL form ends in `-<id>`).
    const found =
      jobs.find((j) => j.id === key || j.slug === key) ||
      jobs.find((j) => (j.slug || "").endsWith(`-${key}`)) ||
      null

    if (!found) {
      writeError(
        `job "${key}" not found in the current RemoteOK feed (it may have aged out)`,
        "NOT_FOUND",
      )
      return 1
    }

    const detail: JobDetail = {
      ...toResult(found),
      description: found.description ? htmlToText(found.description) : null,
    }

    if (opts.format === "plain") {
      const sal = detail.salaryMax
        ? ` · $${Math.round((detail.salaryMin || 0) / 1000)}-${Math.round(detail.salaryMax / 1000)}k USD/yr`
        : ""
      process.stdout.write(
        `${detail.title}\n${detail.company || "—"} · ${detail.location || "—"} · ${detail.date || "—"}` +
          `${sal}${detail.visa ? " · " + detail.visa : ""}\n${detail.url}\n` +
          `apply: ${detail.applyUrl || detail.url}\n\n${detail.description || "(no description)"}\n`,
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
