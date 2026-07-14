#!/usr/bin/env bun
// Self-contained CLI for the Landing.jobs public API v1 (JSON, no auth, zero
// runtime dependencies). EU-focused tech board; many roles are relocation/visa
// friendly (`relocation_paid`). Mirrors the repo's portal-skill contract.

import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"

interface Flags {
  _: string[]
  [k: string]: string | boolean | string[]
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] }
  const alias: Record<string, string> = { q: "query", l: "location", n: "limit" }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a.startsWith("--") || a.startsWith("-")) {
      const key = alias[a.replace(/^-+/, "")] ?? a.replace(/^-+/, "")
      const next = argv[i + 1]
      if (next === undefined || next.startsWith("-")) {
        flags[key] = true
      } else {
        flags[key] = next
        i++
      }
    } else {
      ;(flags._ as string[]).push(a)
    }
  }
  return flags
}

const HELP = `landingjobs-cli — search jobs on the Landing.jobs public API (EU tech, relocation-friendly)

USAGE
  bun run src/cli.ts search [flags]
  bun run src/cli.ts detail <id|url> [--format json|plain]

SEARCH FLAGS
  --query, -q <text>      Keywords (title/tags/requirements/description). AND semantics.
  --location, -l <text>   Filter by location substring (client-side). Optional.
  --remote                Only remote jobs.
  --visa                  Only jobs flagged relocation_paid or hinting visa/relocation.
  --min-salary <n>        Only jobs whose known annual gross max is >= this floor
                          (in the posting's currency, mostly EUR; unknown kept).
  --jobage <days>         Only jobs posted within N days. Default: all.
  --page <n>              1-indexed start page. Default 1.
  --limit, -n <n>         Cap results emitted. Default 50.
  --format <fmt>          json (default) | table | plain.

EXAMPLES
  bun run src/cli.ts search -q "backend developer" --format table
  bun run src/cli.ts search -q java --visa --format table
  bun run src/cli.ts search -q python --remote -l Berlin
  bun run src/cli.ts detail 19066 --format plain

Public API. Salaries are annual gross in the posting's currency. Errors -> stderr, exit 1.
`

async function main(): Promise<number> {
  const argv = process.argv.slice(2)
  const flags = parseFlags(argv)
  const cmd = (flags._ as string[])[0]

  if (!cmd || flags.help || flags.h) {
    process.stdout.write(HELP)
    return cmd ? 0 : 1
  }

  if (cmd === "search") {
    const fmt = (flags.format as string) || "json"

    const parseIntFlag = (name: string, raw: string | boolean | string[]): number | null => {
      const val = parseInt(raw as string, 10)
      if (isNaN(val)) {
        writeErr(`--${name} must be a number, got "${raw}"`, "BAD_ARG")
        return null
      }
      return val
    }

    for (const key of ["jobage", "page", "limit", "min-salary"] as const) {
      if (flags[key] !== undefined && typeof flags[key] !== "boolean") {
        const v = parseIntFlag(key, flags[key])
        if (v === null) return 1
        flags[key] = String(v)
      }
    }

    const opts: SearchOpts = {
      query: typeof flags.query === "string" ? flags.query : undefined,
      location: typeof flags.location === "string" ? flags.location : undefined,
      remote: flags.remote === true || flags.remote === "true",
      visa: flags.visa === true || flags.visa === "true",
      minSalary: typeof flags["min-salary"] === "string" ? parseInt(flags["min-salary"], 10) : undefined,
      jobage: typeof flags.jobage === "string" ? parseInt(flags.jobage, 10) : 9999,
      page: typeof flags.page === "string" ? Math.max(1, parseInt(flags.page, 10)) : 1,
      limit: typeof flags.limit === "string" ? parseInt(flags.limit, 10) : undefined,
      format: (["json", "table", "plain"].includes(fmt) ? fmt : "json") as SearchOpts["format"],
    }
    return runSearch(opts)
  }

  if (cmd === "detail") {
    const id = (flags._ as string[])[1]
    if (!id) {
      writeErr("detail requires an <id|url>", "NO_ID")
      return 1
    }
    const fmt = (flags.format as string) || "json"
    const opts: DetailOpts = {
      id,
      format: (fmt === "plain" ? "plain" : "json") as DetailOpts["format"],
    }
    return runDetail(opts)
  }

  writeErr(`Unknown command "${cmd}"`, "BAD_CMD")
  return 1
}

function writeErr(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

main().then((code) => process.exit(code))
