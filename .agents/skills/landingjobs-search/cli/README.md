# landingjobs-cli

Self-contained CLI for the [Landing.jobs](https://landing.jobs) public API v1.
EU tech, relocation/visa-friendly. Zero runtime dependencies — runs with `bun`.
See `../SKILL.md` for full docs.

## Setup

```bash
bun install    # optional: only pulls TypeScript dev types
```

## Usage

```bash
bun run src/cli.ts search -q "backend developer" --format table
bun run src/cli.ts search -q java --visa
bun run src/cli.ts detail 19066 --format plain
```

## Develop

```bash
bun run typecheck
bun test
```
