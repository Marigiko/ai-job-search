# remotive-cli

Self-contained CLI for the [Remotive](https://remotive.com) public API.
Remote-only, server-side search. Zero runtime dependencies — runs with `bun`.
See `../SKILL.md` for full docs.

## Usage

```bash
bun run src/cli.ts search -q "backend developer" --format table
bun run src/cli.ts search -q python -l "Europe"
bun run src/cli.ts detail 2091062 --format plain
```

## Develop

```bash
bun install
bun run typecheck
bun test
```
