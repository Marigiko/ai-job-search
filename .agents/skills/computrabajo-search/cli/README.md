# computrabajo-cli

Self-contained CLI for [Computrabajo](https://ar.computrabajo.com) public search pages (HTML).
LatAm, default Argentina. Zero runtime dependencies — runs with `bun`. See `../SKILL.md` for full docs.

**Personal use only** (Computrabajo ToS) — keep volume low.

## Usage

```bash
bun run src/cli.ts search -q "desarrollador" -c ar --format table
bun run src/cli.ts search -q "backend developer" -c ar -l "Buenos Aires"
bun run src/cli.ts detail "https://ar.computrabajo.com/ofertas-de-trabajo/...-ABC123" --format plain
```

## Develop

```bash
bun install
bun run typecheck
bun test
```
