# .opencode/skills/

This directory is a **parity mirror** of `.claude/skills/` for OpenCode and MiMoCode compatibility.

## How it works

- **Claude Code** discovers skills from `.claude/skills/*/SKILL.md` and `.agents/skills/*/SKILL.md`.
- **MiMoCode** discovers skills from `.claude/skills/*/`, `.agents/skills/*/`, `.codex/skills/*/`, and `.opencode/skills/*/`.
- **OpenCode** discovers skills from `.opencode/skills/*/SKILL.md` (its native path).

The 10 command-derived skills (`apply`, `setup`, `outcome`, `rank`, `interview`, `expand`, `reset`, `add-template`, `add-portal`, `dashboard`) exist in BOTH `.claude/skills/` and `.opencode/skills/` so all three harnesses discover them. The 3 original skills (`job-application-assistant`, `job-scraper`, `upskill`) live in `.claude/skills/` and are also mirrored here.

## Rule

When adding or modifying a skill that originates from a `.claude/commands/*.md` file, mirror the change to BOTH directories. The CI lint (`tools/lint_skills.py`) enforces parity — it fails if a skill exists in one directory but not the other.

The `.claude/commands/*.md` files remain the canonical source for Claude Code slash commands. The SKILL.md files are derived from them with two differences:
1. YAML frontmatter (`name`, `description`, `allowed-tools`) is added.
2. `$ARGUMENTS` references are replaced with natural-language prompts (skills don't receive arguments via shell expansion).
