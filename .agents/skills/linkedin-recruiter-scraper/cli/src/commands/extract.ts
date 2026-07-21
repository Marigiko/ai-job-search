import {
  writeError,
  buildFromPostUrl,
  extractEmails,
  synthTitle,
  activityIdFromUrl,
  dateFromActivityId,
  writeOutput,
  type PostResult,
} from "../helpers.js"

export interface ExtractOpts {
  url?: string
  text?: string
}

const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

async function htmlFetch(url: string): Promise<string> {
  const maxRetries = 3
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      headers: {
        "User-Agent": UA,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      },
      redirect: "follow",
    })
    if (response.status === 429 || response.status >= 500) {
      if (attempt === maxRetries) return ""
      await new Promise((r) => setTimeout(r, delay))
      delay *= 2
      continue
    }
    if (!response.ok) return ""
    return response.text()
  }
  return ""
}

function meta(html: string, prop: string): string | null {
  const patterns = [
    new RegExp(`<meta[^>]+property="${prop}"[^>]+content="([^"]*)"`, "i"),
    new RegExp(`<meta[^>]+content="([^"]*)"[^>]+property="${prop}"`, "i"),
    new RegExp(`<meta[^>]+name="${prop}"[^>]+content="([^"]*)"`, "i"),
  ]
  for (const p of patterns) {
    const m = html.match(p)
    if (m) return m[1]
  }
  return null
}

function buildFromHtml(html: string, url: string): PostResult {
  const ogDesc = meta(html, "og:description") || meta(html, "description")
  const id = activityIdFromUrl(url)
  const emails = extractEmails(html)
  return {
    id: id || url,
    title: synthTitle(ogDesc, url),
    company: null,
    location: null,
    date: dateFromActivityId(id),
    url: url.split("?")[0],
    applyEmail: emails[0] ?? null,
    emails,
    author: null,
    text: ogDesc ? ogDesc.trim().slice(0, 4000) : null,
    source: "linkedin-recruiter-post",
  }
}

function render(result: PostResult): void {
  writeOutput({ meta: { count: 1 }, results: [result] })
}

export async function runExtract(opts: ExtractOpts): Promise<number> {
  try {
    if (opts.text) {
      const emails = extractEmails(opts.text)
      const id = opts.url ? activityIdFromUrl(opts.url) : null
      render({
        id: id || opts.url || "pasted-post",
        title: synthTitle(opts.text, "Pasted post"),
        company: null,
        location: null,
        date: dateFromActivityId(id),
        url: opts.url ? opts.url.split("?")[0] : "",
        applyEmail: emails[0] ?? null,
        emails,
        author: null,
        text: opts.text.trim().slice(0, 4000),
        source: "linkedin-recruiter-post",
      })
      return 0
    }
    if (!opts.url) {
      writeError("extract needs a <post-url> or --text \"<pasted post>\"", "NO_INPUT")
      return 1
    }
    const html = await htmlFetch(opts.url)
    if (!html) {
      writeError(`could not fetch "${opts.url}". Use parse --text instead.`, "NOT_FOUND")
      return 1
    }
    const result = buildFromHtml(html, opts.url)
    if (!result.text && result.emails.length === 0) {
      writeError(`fetched but no content/email. Paste text with parse --text.`, "NO_CONTENT")
      return 1
    }
    render(result)
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "EXTRACT_FAILED")
    return 1
  }
}
