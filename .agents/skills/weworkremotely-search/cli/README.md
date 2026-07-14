# weworkremotely-cli

Self-contained CLI for [We Work Remotely](https://weworkremotely.com) public RSS feeds.
Zero runtime dependencies — runs with `bun`. See `../SKILL.md` for full docs.

## Setup

```bash
bun install    # optional: only pulls TypeScript dev types
```

## Usage

```bash
bun run src/cli.ts search -q "backend" --format table
bun run src/cli.ts search -q "react" -c front-end
bun run src/cli.ts detail <slug|url> --format plain
```

## Develop

```bash
bun run typecheck
bun test
```
