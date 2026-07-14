#!/usr/bin/env bun
// Self-contained CLI for The Muse public jobs API (JSON, no auth/key, zero
// runtime dependencies). US-strong but global via the `--location` filter
// (e.g. "New York, NY", "Auckland, New Zealand", "London, United Kingdom").

import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"

interface Flags {
  _: string[]
  [k: string]: string | boolean | string[]
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] }
  const alias: Record<string, string> = { q: "query", l: "location", n: "limit", c: "category" }
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

const HELP = `themuse-cli — search jobs on The Muse public API (US-strong, global via --location)

USAGE
  bun run src/cli.ts search [flags]
  bun run src/cli.ts detail <id> [--format json|plain]

SEARCH FLAGS
  --query, -q <text>      Keywords (client-side; The Muse API has no keyword param).
  --location, -l <text>   Location, e.g. "New York, NY", "Auckland, New Zealand",
                          "London, United Kingdom", "Flexible / Remote". Server-side.
  --category, -c <text>   Category, e.g. "Software Engineering", "Data Science". Server-side.
  --level <text>          Level, e.g. "Mid Level", "Senior Level", "Entry Level".
  --visa                  Only jobs whose text hints at visa sponsorship / relocation.
  --page <n>              1-indexed start page. Default 1.
  --limit, -n <n>         Cap results emitted. Default 50.
  --format <fmt>          json (default) | table | plain.

EXAMPLES
  bun run src/cli.ts search -c "Software Engineering" -l "New York, NY" --format table
  bun run src/cli.ts search -q backend -l "Auckland, New Zealand" --format table
  bun run src/cli.ts search -q engineer -l "London, United Kingdom"
  bun run src/cli.ts detail 21610367 --format plain

Public API, no key. Errors -> stderr { "error", "code" }, exit 1.
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
    for (const key of ["page", "limit"] as const) {
      if (flags[key] !== undefined && typeof flags[key] !== "boolean") {
        const v = parseInt(flags[key] as string, 10)
        if (isNaN(v)) {
          writeErr(`--${key} must be a number, got "${flags[key]}"`, "BAD_ARG")
          return 1
        }
        flags[key] = String(v)
      }
    }
    const opts: SearchOpts = {
      query: typeof flags.query === "string" ? flags.query : undefined,
      location: typeof flags.location === "string" ? flags.location : undefined,
      category: typeof flags.category === "string" ? flags.category : undefined,
      level: typeof flags.level === "string" ? flags.level : undefined,
      visa: flags.visa === true || flags.visa === "true",
      page: typeof flags.page === "string" ? Math.max(1, parseInt(flags.page, 10)) : 1,
      limit: typeof flags.limit === "string" ? parseInt(flags.limit, 10) : undefined,
      format: (["json", "table", "plain"].includes(fmt) ? fmt : "json") as SearchOpts["format"],
    }
    return runSearch(opts)
  }

  if (cmd === "detail") {
    const id = (flags._ as string[])[1]
    if (!id) {
      writeErr("detail requires an <id>", "NO_ID")
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
