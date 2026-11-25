# Claude Code

Only `CLAUDE.md` is tracked. It links to `~/.claude/CLAUDE.md` and imports the shared instructions, which are linked alongside it as `~/.claude/AGENTS.md`. Shared skills are merged into `~/.claude/skills/`.

Settings stay at Claude Code's defaults and are not tracked.

The import is the only way the shared instructions reach Claude Code globally: its native `AGENTS.md` support is a project-level fallback, and the user-level `~/.claude/CLAUDE.md` always loads without triggering it. The import is written as the absolute `@~/.claude/AGENTS.md` because a relative path would resolve against the symlink target.
