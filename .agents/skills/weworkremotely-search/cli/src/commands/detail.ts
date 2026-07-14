import {
  feedUrl,
  CATEGORIES,
  textFetch,
  parseItems,
  htmlToText,
  toResult,
  writeError,
  type JobDetail,
  type RawItem,
} from "../helpers.js"

export interface DetailOpts {
  id: string // WWR job slug or full job URL
  category?: string
  format: "json" | "plain"
}

function slugOf(idOrUrl: string): string {
  const m = idOrUrl.match(/remote-jobs\/([^/?#]+)/)
  return m ? m[1] : idOrUrl.replace(/[/?#].*$/, "")
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  try {
    const slug = slugOf(opts.id)
    // The RSS carries the full description inline. If a category is known, use it;
    // otherwise scan the common category feeds until the slug is found.
    const cats = opts.category ? [opts.category] : Object.keys(CATEGORIES)
    let match: RawItem | null = null
    for (const cat of cats) {
      const xml = await textFetch(feedUrl(cat))
      if (!xml) continue
      const items = parseItems(xml)
      match =
        items.find((it) => (it.link || it.guid || "").includes(slug)) || null
      if (match) break
    }

    if (!match) {
      writeError(`job "${slug}" not found in the current WWR feeds`, "NOT_FOUND")
      return 1
    }

    const detail: JobDetail = {
      ...toResult(match),
      description: match.description ? htmlToText(match.description) : null,
    }

    if (opts.format === "plain") {
      process.stdout.write(
        `${detail.title}\n${detail.company || "—"} · ${detail.location || "—"} · ${detail.date || "—"}` +
          `${detail.visa ? " · " + detail.visa : ""}\n${detail.url}\n\n${detail.description || "(no description)"}\n`,
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
