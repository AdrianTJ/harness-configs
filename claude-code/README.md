# Claude Code

Config root: `~/.claude/` (project-level equivalent: `.claude/` in a repo).

| Repo path | Links to | What it is |
|---|---|---|
| `settings.json` | `~/.claude/settings.json` | Permissions, hooks, env, model. |
| `agents/` | `~/.claude/agents/` | Subagent definitions (markdown + frontmatter). |
| `commands/` | `~/.claude/commands/` | Slash commands. |
| `skills/` | `~/.claude/skills/` | Claude-Code-only skills; portable ones come from `shared/skills/`. |

`~/.claude/CLAUDE.md` is a symlink to `shared/AGENTS.md`, so the same global
instructions apply here as in pi, codex, and opencode.

## settings.json vs settings.local.json

Claude Code writes machine-local permission grants into `settings.local.json`.
That file is gitignored and never linked — keep the durable, portable rules in
`settings.json` here and let the local file stay local.

## Not linked

`.credentials.json`, `history.jsonl`, `projects/`, `todos/`, and `statsig/` are
runtime state. `plugins/` is managed by Claude Code's own plugin installer; track
plugin *sources* in `settings.json` rather than linking the installed tree.
