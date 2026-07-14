import { API_BASE, jsonFetch, htmlToText, toResult, writeError, type MuseRaw, type JobDetail } from "../helpers.js"

export interface DetailOpts {
  id: string // The Muse numeric job id
  format: "json" | "plain"
}

function idOf(idOrUrl: string): string {
  const m = idOrUrl.match(/(\d{5,})/)
  return m ? m[1] : idOrUrl.trim()
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  try {
    const id = idOf(opts.id)
    // The Muse exposes a per-job endpoint: /api/public/jobs/<id>
    const raw: MuseRaw | null = await jsonFetch(`${API_BASE}/${id}`)
    if (!raw || !raw.id) {
      writeError(`job "${id}" not found on The Muse`, "NOT_FOUND")
      return 1
    }

    const detail: JobDetail = {
      ...toResult(raw),
      description: raw.contents ? htmlToText(raw.contents) : null,
    }

    if (opts.format === "plain") {
      process.stdout.write(
        `${detail.title}\n${detail.company || "—"} · ${detail.location || "—"} · ${detail.date || "—"}` +
          `${detail.level ? " · " + detail.level : ""}${detail.remote ? " · remote" : ""}${detail.visa ? " · " + detail.visa : ""}\n` +
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
