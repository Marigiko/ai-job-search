#!/usr/bin/env bun
import { runSearch } from "./commands/search.js"

const args = process.argv.slice(2)
const command = args[0] || "search"
const rest = command === "search" ? args.slice(1) : args

if (command !== "search") {
  console.error(`Unknown command: ${command}`)
  console.error("Usage: bun run cli.ts search [--role <role>] [--remote] [--batch <batch>] [--max-results <n>] [--engine google|bing]")
  process.exit(1)
}

function parseOpts(args: string[]): Record<string, string> {
  const opts: Record<string, string> = {}
  for (let i = 0; i < args.length; i++) {
    const arg = args[i]
    if (arg.startsWith("--") && args[i + 1] && !args[i + 1].startsWith("--")) {
      opts[arg.slice(2)] = args[++i]
    } else if (arg === "--remote") {
      opts.remote = "true"
    }
  }
  return opts
}

const opts = parseOpts(rest)
const code = await runSearch({
  role: opts.role,
  remote: opts.remote === "true",
  batch: opts.batch,
  maxResults: opts.maxResults || "10",
  engine: opts.engine === "google" ? "google" : "bing",
})
process.exit(code)
