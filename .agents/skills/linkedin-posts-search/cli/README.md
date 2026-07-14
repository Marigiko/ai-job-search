# linkedin-posts-cli

Extract apply-by-email leads from public LinkedIn post permalinks (or pasted text).
Zero runtime dependencies — runs with `bun`. See `../SKILL.md` for full docs.

**Personal use only** (LinkedIn ToS). Fetches only public permalinks you already have; does not crawl the feed.

## Usage

```bash
bun run src/cli.ts extract "https://www.linkedin.com/posts/...-activity-123-abcd" --format plain
bun run src/cli.ts parse --text "Hiring backend dev. Send CV to jobs@acme.com"
cat post.txt | bun run src/cli.ts parse
```

## Develop

```bash
bun install
bun run typecheck
bun test
```
