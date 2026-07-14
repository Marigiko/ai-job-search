# arbeitnow-cli

Self-contained CLI for the [Arbeitnow](https://www.arbeitnow.com) public job-board API.
Zero runtime dependencies — runs with `bun`. See the skill's `../SKILL.md` for full docs.

## Setup

```bash
bun install    # optional: only pulls TypeScript dev types
```

## Usage

```bash
bun run src/cli.ts search -q "backend developer" --remote --format table
bun run src/cli.ts search -q "ai engineer" --visa
bun run src/cli.ts detail <slug|url> --format plain
```

## Develop

```bash
bun run typecheck
bun test
```
