#!/usr/bin/env bun
// Self-contained CLI for We Work Remotely public RSS category feeds (XML, no auth,
// zero runtime dependencies). Mirrors the repo's portal-skill contract. Every WWR
// listing is remote.

import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"
import { CATEGORIES } from "./helpers.js"

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

const HELP = `weworkremotely-cli — search remote jobs on We Work Remotely RSS feeds (all remote)

USAGE
  bun run src/cli.ts search [flags]
  bun run src/cli.ts detail <slug|url> [--category <cat>] [--format json|plain]

SEARCH FLAGS
  --query, -q <text>      Keywords (title/region/category/description). AND semantics.
  --location, -l <text>   Filter by region substring (client-side). Optional.
  --category, -c <cat>    Feed to search. Default: programming.
                          Options: ${Object.keys(CATEGORIES).join(", ")}
  --visa                  Only jobs whose text hints at visa sponsorship / relocation.
  --limit, -n <n>         Cap results emitted (client-side). Default 50.
  --format <fmt>          json (default) | table | plain.

EXAMPLES
  bun run src/cli.ts search -q "backend" --format table
  bun run src/cli.ts search -q "react" -c front-end --format table
  bun run src/cli.ts search -q "engineer" --visa
  bun run src/cli.ts detail company-position-slug --format plain

Public RSS. Errors -> stderr { "error", "code" }, exit 1.
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
    if (flags.limit !== undefined && typeof flags.limit !== "boolean") {
      const v = parseInt(flags.limit as string, 10)
      if (isNaN(v)) {
        writeErr(`--limit must be a number, got "${flags.limit}"`, "BAD_ARG")
        return 1
      }
      flags.limit = String(v)
    }
    const opts: SearchOpts = {
      query: typeof flags.query === "string" ? flags.query : undefined,
      location: typeof flags.location === "string" ? flags.location : undefined,
      visa: flags.visa === true || flags.visa === "true",
      category: typeof flags.category === "string" ? flags.category : "programming",
      limit: typeof flags.limit === "string" ? parseInt(flags.limit, 10) : undefined,
      format: (["json", "table", "plain"].includes(fmt) ? fmt : "json") as SearchOpts["format"],
    }
    return runSearch(opts)
  }

  if (cmd === "detail") {
    const id = (flags._ as string[])[1]
    if (!id) {
      writeErr("detail requires a <slug|url>", "NO_ID")
      return 1
    }
    const fmt = (flags.format as string) || "json"
    const opts: DetailOpts = {
      id,
      category: typeof flags.category === "string" ? flags.category : undefined,
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
