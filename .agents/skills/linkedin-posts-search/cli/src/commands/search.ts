import { writeError } from "../helpers.js"

export interface SearchOpts {
  query?: string
  format: "json" | "plain"
}

/**
 * Feed keyword search requires a logged-in LinkedIn session (Voyager API), which
 * the repo's public-only pattern deliberately avoids. This command therefore does
 * NOT crawl the feed. It documents the compliant workflow and, if the user has
 * explicitly opted into the authenticated mode by exporting LINKEDIN_COOKIE, tells
 * them it is their responsibility (still not implemented here to avoid shipping a
 * ToS-violating crawler by default).
 */
export async function runSearch(opts: SearchOpts): Promise<number> {
  const authed = Boolean(process.env.LINKEDIN_COOKIE)
  const guidance =
    "Recruiter-post keyword search needs a logged-in LinkedIn session, which this skill does not do. " +
    "Compliant workflow: discover public post permalinks with WebSearch " +
    '(e.g. site:linkedin.com/posts "send your CV" <role> <location>), then run ' +
    "`extract <post-url>` on each. If you already have the post text, use `parse --text \"<text>\"`."
  writeError(
    authed
      ? "LINKEDIN_COOKIE is set, but authenticated feed search is intentionally not implemented (against LinkedIn ToS). " +
          guidance
      : guidance,
    "NEEDS_DISCOVERY",
  )
  return 1
}
