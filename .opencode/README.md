# .opencode/ — OpenCode / MiMoCode Skill Parity

This directory mirrors the `.claude/skills/` tree so that OpenCode and MiMoCode
discover the same skills Claude Code discovers via `.claude/skills/` and
`.claude/commands/`.

## Layout

```
.opencode/
├── README.md     # this file
└── skills/       # SKILL.md pair for every skill in .claude/skills/
    ├── apply/SKILL.md
    ├── setup/SKILL.md
    ├── ... (one directory per skill)
```

## How it works

- **MiMoCode** discovers skills from `.claude/skills/**`, `.agents/skills/`,
  `.codex/skills/**`, **and** `.opencode/skills/**`. Putting skills here makes
  them available on MiMoCode without needing the `.claude/` prefix.
- **OpenCode** reads `.opencode/skills/**` as its native skill location.
- **Claude Code** reads `.claude/skills/**` and `.claude/commands/**`.

The `.claude/commands/*.md` files (slash commands like `/apply`) remain for Claude
Code users. The skills under `.opencode/skills/` are conversions of the same
commands, adapted for the skill-based invocation model (no `$ARGUMENTS`,
natural-language triggers).

## Rule: parity

Every skill in `.claude/skills/<name>/SKILL.md` MUST have a corresponding
`.opencode/skills/<name>/SKILL.md`. The two files must be identical in content.
Run `python3 tools/lint_skills.py` to verify parity — it fails if the two trees
drift apart.

The portal-specific skills in `.agents/skills/` (jobindex-search, linkedin-search,
etc.) are NOT duplicated here — MiMoCode/OpenCode discover them via
`.agents/skills/**` directly.
