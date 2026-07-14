# themuse-cli

Self-contained CLI for [The Muse](https://www.themuse.com) public jobs API.
US-strong but global via `--location`. Zero runtime dependencies — runs with `bun`.
See `../SKILL.md` for full docs.

## Usage

```bash
bun run src/cli.ts search -c "Software Engineering" -l "New York, NY" --format table
bun run src/cli.ts search -q backend -l "Auckland, New Zealand"
bun run src/cli.ts detail 21610367 --format plain
```

## Develop

```bash
bun install
bun run typecheck
bun test
```
