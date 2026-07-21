#!/usr/bin/env bun
// LinkedIn recruiter post CLI — discover posts with apply-by-email addresses
// via public search engines, then extract. No LinkedIn authentication.
//
// Personal use only. Public permalinks only. Keep volume low.

import { runSearch, type SearchOptions } from "./commands/search.js"
import { runExtract, type ExtractOpts } from "./commands/extract.js"

interface Flags {
  _: string[]
  [k: string]: string | boolean | string[]
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] }
  const alias: Record<string, string> = { q: "query", u: "url", t: "text", m: "max-results", e: "engine" }
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

const HELP = `linkedin-recruiter-cli — discover LinkedIn recruiter posts by email

USAGE
  bun run src/cli.ts search --query <terms> [--max-results N] [--engine google|bing]
  bun run src/cli.ts extract <post-url>
  bun run src/cli.ts parse --text "<pasted post text>" [--url <post-url>]

COMMANDS
  search   Use Playwright + search engines to find LinkedIn post permalinks
  extract  Fetch a public post URL and extract apply-by-email
  parse    Parse pasted post text (offline, reliable fallback)

FLAGS
  --query, -q <terms>     search query (use site:linkedin.com/posts ...)
  --max-results, -m <n>    max LinkedIn posts per query (default 5)
  --engine, -e <name>     google or bing (default bing — fewer CAPTCHAs)
  --url, -u <url>         post URL
  --text, -t <text>       post text to parse

Personal use only (LinkedIn ToS). Errors -> stderr { error, code }, exit 1.
`

async function readStdin(): Promise<string> {
  const chunks: Uint8Array[] = []
  for await (const chunk of Bun.stdin.stream()) chunks.push(chunk)
  return Buffer.concat(chunks).toString("utf8")
}

async function main(): Promise<number> {
  const argv = process.argv.slice(2)
  const flags = parseFlags(argv)
  const cmd = (flags._ as string[])[0]

  if (!cmd || flags.help || flags.h) {
    process.stdout.write(HELP)
    return cmd ? 0 : 1
  }

  if (cmd === "search") {
    const opts: SearchOptions = {
      query: typeof flags.query === "string" ? flags.query : undefined,
      maxResults: typeof flags["max-results"] === "string" ? flags["max-results"] : undefined,
      engine: typeof flags.engine === "string" ? flags.engine : undefined,
    }
    return runSearch(opts)
  }

  if (cmd === "extract") {
    const url = (flags._ as string[])[1] || (typeof flags.url === "string" ? flags.url : undefined)
    const opts: ExtractOpts = {
      url,
      text: typeof flags.text === "string" ? flags.text : undefined,
    }
    return runExtract(opts)
  }

  if (cmd === "parse") {
    let text = typeof flags.text === "string" ? flags.text : undefined
    if (!text && !process.stdin.isTTY) {
      const piped = await readStdin()
      if (piped.trim()) text = piped
    }
    if (!text) {
      process.stderr.write(
        JSON.stringify({ error: 'parse needs --text "<post text>" or piped stdin', code: "NO_INPUT" }) + "\n",
      )
      return 1
    }
    return runExtract({ text, url: typeof flags.url === "string" ? flags.url : undefined })
  }

  process.stderr.write(JSON.stringify({ error: `Unknown command "${cmd}"`, code: "BAD_CMD" }) + "\n")
  return 1
}

main().then((code) => process.exit(code))
