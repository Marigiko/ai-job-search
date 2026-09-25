import { writeError, writeOutput } from "../helpers.js"
import { spawnSync } from "node:child_process"
import { fileURLToPath } from "node:url"
import { dirname, resolve } from "node:path"

export interface SearchOptions {
  query?: string
  maxResults?: string
  engine?: string
}

/**
 * Discover LinkedIn recruiter post URLs via public search engines.
 * Tries Serper API → DuckDuckGo → direct scrape, in that order.
 * Delegates to the Python search module and converts its JSON output into the
 * standard results contract.
 */
export async function runSearch(opts: SearchOptions): Promise<number> {
  const query = opts.query
  if (!query) {
    writeError("search requires --query <search terms>", "NO_QUERY")
    return 1
  }

  const maxResults = opts.maxResults || "5"
  const engine = opts.engine === "google" ? "google" : "bing"

  const here = dirname(fileURLToPath(import.meta.url))
  const pyScript = resolve(here, "..", "..", "..", "search.py")

  const candidates = process.platform === "win32" ? ["python3", "python"] : ["python3"]
  let proc: ReturnType<typeof spawnSync> | null = null
  for (const py of candidates) {
    const r = spawnSync(
      py,
      [pyScript, "--query", query, "--max-results", maxResults, "--engine", engine, "--format", "json"],
      { encoding: "utf-8", timeout: 30_000 },
    )
    if (!r.error) {
      proc = r
      break
    }
  }
  if (!proc) {
    writeError("no python interpreter available. Install Python 3.", "NO_PYTHON")
    return 1
  }

  if (proc.status !== 0) {
    const err = proc.stderr?.trim() || proc.stdout?.trim() || `exit ${proc.status}`
    writeError(err, "SEARCH_FAILED")
    return 1
  }

  try {
    const payload = JSON.parse(proc.stdout)
    writeOutput({ meta: { count: payload.results?.length || 0 }, results: payload.results || [] })
    return 0
  } catch (e) {
    writeError(`could not parse python search output: ${e instanceof Error ? e.message : String(e)}`, "BAD_OUTPUT")
    return 1
  }
}
