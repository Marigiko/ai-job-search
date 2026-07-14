import { htmlFetch, buildFromHtml, buildFromText, writeError, type PostResult } from "../helpers.js"

export interface ExtractOpts {
  url?: string
  text?: string
  format: "json" | "plain"
}

function render(result: PostResult, format: "json" | "plain"): void {
  if (format === "plain") {
    process.stdout.write(
      `${result.title}\n` +
        `${result.author || "—"}${result.date ? " · " + result.date : ""}\n` +
        `${result.url || "(pasted text)"}\n` +
        `apply email: ${result.applyEmail || "(none found)"}\n` +
        (result.emails.length > 1 ? `other emails: ${result.emails.slice(1).join(", ")}\n` : "") +
        `\n${result.text || "(no text)"}\n`,
    )
  } else {
    process.stdout.write(JSON.stringify({ meta: { count: 1 }, results: [result] }, null, 2) + "\n")
  }
}

export async function runExtract(opts: ExtractOpts): Promise<number> {
  try {
    // Text path (reliable, no network): parse a pasted post.
    if (opts.text) {
      render(buildFromText(opts.text, opts.url), opts.format)
      return 0
    }
    if (!opts.url) {
      writeError("extract needs a <post-url> or --text \"<pasted post>\"", "NO_INPUT")
      return 1
    }
    const html = await htmlFetch(opts.url)
    if (!html) {
      writeError(
        `could not fetch "${opts.url}" (404 or removed). If you have the post text, use: parse --text "<text>"`,
        "NOT_FOUND",
      )
      return 1
    }
    const result = buildFromHtml(html, opts.url)
    // If LinkedIn served an auth wall with no usable text/email, say so clearly.
    if (!result.text && result.emails.length === 0) {
      writeError(
        `fetched "${opts.url}" but found no post text or email (LinkedIn may have gated it). ` +
          `Paste the post text instead: parse --text "<text>"`,
        "NO_CONTENT",
      )
      return 1
    }
    render(result, opts.format)
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "EXTRACT_FAILED")
    return 1
  }
}
