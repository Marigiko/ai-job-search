# getonbrd-cli

Self-contained CLI for the [Get on Board](https://www.getonbrd.com) public API v0.
LatAm + remote tech, monthly-USD salaries. Zero runtime dependencies — runs with `bun`.
See `../SKILL.md` for full docs.

## Setup

```bash
bun install    # optional: only pulls TypeScript dev types
```

## Usage

```bash
bun run src/cli.ts search -q "backend developer" --remote --format table
bun run src/cli.ts search -q python --min-salary 2500
bun run src/cli.ts detail <slug|url> --format plain
```

## Develop

```bash
bun run typecheck
bun test
```
