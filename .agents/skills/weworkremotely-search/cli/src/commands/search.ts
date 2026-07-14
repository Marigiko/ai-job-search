import {
  feedUrl,
  textFetch,
  parseItems,
  matchesQuery,
  toResult,
  writeError,
  type JobResult,
} from "../helpers.js"

export interface SearchOpts {
  query?: string
  location?: string
  visa?: boolean
  category: string
  limit?: number
  format: "json" | "table" | "plain"
}

function renderTable(rows: JobResult[]): string {
  if (rows.length === 0) return "No results."
  const line = (r: JobResult) => {
    const title = (r.title || "").slice(0, 40).padEnd(40)
    const company = (r.company || "—").slice(0, 22).padEnd(22)
    const loc = (r.location || "—").slice(0, 20).padEnd(20)
    return `${title} ${company} ${loc} ${(r.date || "—").padEnd(10)} ${r.visa || "—"}`
  }
  const header =
    "TITLE".padEnd(40) + " " + "COMPANY".padEnd(22) + " " + "REGION".padEnd(20) + " DATE       VISA"
  return [header, "-".repeat(header.length), ...rows.map(line)].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const limit = opts.limit !== undefined && opts.limit >= 0 ? opts.limit : 50
    const loc = opts.location?.toLowerCase()
    const xml = await textFetch(feedUrl(opts.category))
    if (!xml) {
      writeError(`no feed for category "${opts.category}"`, "NO_FEED")
      return 1
    }
    const items = parseItems(xml)

    const collected: JobResult[] = []
    for (const item of items) {
      if (!matchesQuery(item, opts.query)) continue
      if (loc && !(item.region || "").toLowerCase().includes(loc)) continue
      const result = toResult(item)
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
              `${r.visa ? " · " + r.visa : ""}\n  ${r.url}`,
          )
          .join("\n\n") + "\n",
      )
    } else {
      process.stdout.write(
        JSON.stringify({ meta: { count: collected.length, page: 1, category: opts.category }, results: collected }, null, 2) + "\n",
      )
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "SEARCH_FAILED")
    return 1
  }
}
