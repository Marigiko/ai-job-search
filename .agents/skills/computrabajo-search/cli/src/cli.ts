#!/usr/bin/env bun
// Self-contained CLI for Computrabajo public search pages (HTML, no auth, zero
// runtime dependencies). Country-scoped (default Argentina). Mirrors the repo's
// portal-skill contract.
//
// Personal use only — reads Computrabajo's public pages; automated access may be
// against their ToS. Keep volume low; own responsibility.

import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"

interface Flags {
  _: string[]
  [k: string]: string | boolean | string[]
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] }
  const alias: Record<string, string> = { q: "query", l: "location", n: "limit", c: "country" }
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

const HELP = `computrabajo-cli — search jobs on Computrabajo (LatAm; default Argentina)

USAGE
  bun run src/cli.ts search [flags]
  bun run src/cli.ts detail <offer-url|/path> [--country ar] [--format json|plain]

SEARCH FLAGS
  --query, -q <text>      Keywords (built into the search URL slug). Recommended.
  --country, -c <code>    Country domain: ar (default), mx, cl, pe, co, uy, ...
  --location, -l <text>   Filter by location substring (client-side). Optional.
  --visa                  Only jobs whose text hints at visa/relocation.
  --page <n>              1-indexed start page. Default 1.
  --limit, -n <n>         Cap results emitted. Default 50.
  --format <fmt>          json (default) | table | plain.

EXAMPLES
  bun run src/cli.ts search -q "desarrollador" -c ar --format table
  bun run src/cli.ts search -q "backend developer" -c ar -l "Buenos Aires"
  bun run src/cli.ts detail "https://ar.computrabajo.com/ofertas-de-trabajo/...-ABC123" --format plain

Personal use only (Computrabajo ToS). Errors -> stderr { "error", "code" }, exit 1.
`

async function main(): Promise<number> {
  const argv = process.argv.slice(2)
  const flags = parseFlags(argv)
  const cmd = (flags._ as string[])[0]

  if (!cmd || flags.help || flags.h) {
    process.stdout.write(HELP)
    return cmd ? 0 : 1
  }

  const country = typeof flags.country === "string" ? flags.country : "ar"

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
      country,
      location: typeof flags.location === "string" ? flags.location : undefined,
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
      writeErr("detail requires an <offer-url|/path>", "NO_ID")
      return 1
    }
    const fmt = (flags.format as string) || "json"
    const opts: DetailOpts = {
      id,
      country,
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
