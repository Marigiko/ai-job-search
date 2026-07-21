#!/usr/bin/env bun
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { writeError, writeOutput } from "./helpers.js";

const here = dirname(fileURLToPath(import.meta.url));
const fetcher = resolve(here, "..", "fetcher.py");

function run_fetch(args: string[]): { code: number; stdout: string; stderr: string } {
  const python = process.platform === "win32" ? "python3" : "python3";
  const r = spawnSync(python, [fetcher, ...args], { encoding: "utf-8", timeout: 120_000 });
  return { code: r.status ?? 1, stdout: (r.stdout || "").trim(), stderr: (r.stderr || "").trim() };
}

function main(): number {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (!cmd || cmd === "help") {
    process.stdout.write(
      `telegram-search CLI — fetch jobs from Telegram groups\n\nUSAGE\n  bun run cli/src/cli.ts fetch --group <name> [--limit N]\n  bun run cli/src/cli.ts dialogs [--limit N]\n  bun run cli/src/cli.ts listen --groups "g1,g2"\n  bun run cli/src/cli.ts parse --text "<text>"\n  bun run cli/src/cli.ts auth\n`,
    );
    return cmd ? 0 : 1;
  }

  if (cmd === "parse") {
    const textIdx = args.indexOf("--text");
    if (textIdx === -1 || !args[textIdx + 1]) {
      writeError("parse --text \"<post text>\"", "NO_INPUT");
      return 1;
    }
    const { code, stdout, stderr } = run_fetch(["parse", "--text", args[textIdx + 1]]);
    if (code !== 0) {
      writeError(stderr || "parse failed", "PARSE_ERROR");
      return 1;
    }
    writeOutput(JSON.parse(stdout));
    return 0;
  }

  const pyArgs = args;
  const { code, stdout, stderr } = run_fetch(pyArgs);
  if (code !== 0) {
    writeError(stderr || `exit ${code}`, "FETCH_FAILED");
    return 1;
  }
  try {
    writeOutput(JSON.parse(stdout));
  } catch {
    process.stdout.write(stdout + "\n");
  }
  return 0;
}

process.exit(main());
