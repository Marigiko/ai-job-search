#!/usr/bin/env bun
// Self-contained CLI for extracting apply-by-email job leads from PUBLIC LinkedIn
// post permalinks (or pasted post text). Zero runtime dependencies.
//
// Personal use only. Fetches only public /posts/ permalinks you already have
// (discover via WebSearch, not by crawling the feed). Keep volume low; own
// responsibility. Feed keyword search (authenticated) is intentionally not done.

import { runExtract, type ExtractOpts } from "./commands/extract.js"
import { runSearch, type SearchOpts } from "./commands/search.js"

interface Flags {
  _: string[]
  [k: string]: string | boolean | string[]
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] }
  const alias: Record<string, string> = { q: "query", t: "text", u: "url" }
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

const HELP = `linkedin-posts-cli — extract apply-by-email leads from public LinkedIn posts

USAGE
  bun run src/cli.ts extract <post-url> [--format json|plain]
  bun run src/cli.ts parse --text "<pasted post text>" [--url <post-url>] [--format json|plain]
  bun run src/cli.ts parse < post.txt              # read pasted text from stdin
  bun run src/cli.ts search -q "<keywords>"        # explains the discovery workflow

WHAT IT DOES
  Fetches a PUBLIC LinkedIn post permalink (returns 200 logged-out), reads the
  Open Graph title/description + body, decodes the post date from the activity id,
  and extracts the apply-by-email address (handling [at]/[dot]/&#64; obfuscation).
  If LinkedIn gates a post, paste its text with \`parse --text\`.

FLAGS
  --format <fmt>   json (default) | plain
  --text, -t <s>   post text to parse (parse command)
  --url, -u <url>  the post URL (optional with parse, used for id/date)

Personal use only (LinkedIn ToS). Discover permalinks via WebSearch, then extract.
Errors -> stderr { "error", "code" }, exit 1.
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

  const fmt = (flags.format as string) === "plain" ? "plain" : "json"

  if (cmd === "extract") {
    const url = (flags._ as string[])[1] || (typeof flags.url === "string" ? flags.url : undefined)
    const opts: ExtractOpts = {
      url,
      text: typeof flags.text === "string" ? flags.text : undefined,
      format: fmt as ExtractOpts["format"],
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
    const opts: ExtractOpts = {
      url: typeof flags.url === "string" ? flags.url : undefined,
      text,
      format: fmt as ExtractOpts["format"],
    }
    return runExtract(opts)
  }

  if (cmd === "search") {
    const opts: SearchOpts = {
      query: typeof flags.query === "string" ? flags.query : undefined,
      format: fmt as SearchOpts["format"],
    }
    return runSearch(opts)
  }

  process.stderr.write(JSON.stringify({ error: `Unknown command "${cmd}"`, code: "BAD_CMD" }) + "\n")
  return 1
}

main().then((code) => process.exit(code))
