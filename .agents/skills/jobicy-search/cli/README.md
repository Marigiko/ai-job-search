# jobicy-cli

Self-contained CLI for the [Jobicy](https://jobicy.com) public API v2.
Remote board with region (`--geo`) filtering (USA / New Zealand / Europe / …) and salary bands.
Zero runtime dependencies — runs with `bun`. See `../SKILL.md` for full docs.

## Usage

```bash
bun run src/cli.ts search -q developer -g usa --format table
bun run src/cli.ts search -q engineer -g new-zealand
bun run src/cli.ts detail 149243 --format plain
```

## Develop

```bash
bun install
bun run typecheck
bun test
```
