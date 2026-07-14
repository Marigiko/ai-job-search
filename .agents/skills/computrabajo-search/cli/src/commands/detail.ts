import {
  baseUrl,
  htmlFetch,
  parseCards,
  parseDetailDescription,
  parseOfferHeader,
  detectVisa,
  writeError,
  type JobDetail,
} from "../helpers.js"

export interface DetailOpts {
  id: string // full offer URL, or a /ofertas-de-trabajo/... path, or an offer hex id
  country: string
  format: "json" | "plain"
}

function resolveUrl(idOrUrl: string, base: string): string | null {
  if (/^https?:\/\//.test(idOrUrl)) return idOrUrl.split("#")[0]
  if (idOrUrl.startsWith("/")) return base + idOrUrl.split("#")[0]
  return null // a bare hex id can't be turned into a URL without the slug
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  try {
    const base = baseUrl(opts.country)
    const url = resolveUrl(opts.id, base)
    if (!url) {
      writeError(
        "Computrabajo detail needs the offer URL or /ofertas-de-trabajo/... path (a bare id can't be resolved). Pass the `url` from a search result.",
        "NEED_URL",
      )
      return 1
    }

    const html = await htmlFetch(url)
    if (!html) {
      writeError(`offer at "${url}" not found (it may have expired)`, "NOT_FOUND")
      return 1
    }

    // The offer page also renders its own card header — reuse parseCards to get
    // title/company/location/date, and pull the long description separately.
    const cards = parseCards(html, base)
    const head = cards[0]
    const description = parseDetailDescription(html)

    let detail: JobDetail
    if (head) {
      detail = { ...head, url, description }
    } else {
      const hdr = parseOfferHeader(html)
      detail = {
        id: url,
        title: hdr.title || "(title unavailable)",
        company: hdr.company,
        location: hdr.location,
        date: null,
        url,
        remote: /remoto|teletrabajo|home ?office/i.test(description || ""),
        visa: detectVisa(`${hdr.title ?? ""} ${description ?? ""}`),
        posted: null,
        source: "computrabajo",
        description,
      }
    }

    if (opts.format === "plain") {
      process.stdout.write(
        `${detail.title}\n${detail.company || "—"} · ${detail.location || "—"} · ${detail.posted || detail.date || "—"}` +
          `${detail.remote ? " · remote" : ""}${detail.visa ? " · " + detail.visa : ""}\n${detail.url}\n\n` +
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
