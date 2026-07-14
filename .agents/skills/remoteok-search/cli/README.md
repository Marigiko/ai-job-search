# remoteok-cli

Self-contained CLI for the [RemoteOK](https://remoteok.com) public API.
Zero runtime dependencies — runs with `bun`. See `../SKILL.md` for full docs.

Attribution: RemoteOK asks that you keep the job `url` and credit Remote OK as the source.

## Setup

```bash
bun install    # optional: only pulls TypeScript dev types
```

## Usage

```bash
bun run src/cli.ts search -q "backend developer" --format table
bun run src/cli.ts search -q python --min-salary 36000
bun run src/cli.ts detail 1134769 --format plain
```

## Develop

```bash
bun run typecheck
bun test
```
