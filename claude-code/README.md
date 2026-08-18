# Claude Code

Config root: `~/.claude/` (project-level equivalent: `.claude/` in a repo).

| Repo path | Links to | What it is |
|---|---|---|
| `settings.json` | `~/.claude/settings.json` | Permissions, hooks, env, model. |
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | Imports the shared instructions, then adds Claude-only rules. |
| `agents/` | `~/.claude/agents/` | Subagent definitions (markdown + frontmatter). |
| `commands/` | `~/.claude/commands/` | Slash commands. |
| `skills/` | `~/.claude/skills/` | Claude-Code-only skills; portable ones come from `shared/skills/`. |

`CLAUDE.md` here is a real file, not a symlink. It imports `shared/AGENTS.md`
(linked alongside it as `~/.claude/AGENTS.md`) and then adds the rules that only
apply to Claude Code. Claude Code reads `CLAUDE.md` and not `AGENTS.md`, so the
shared half loads exactly once.

The import is written as an absolute `@~/.claude/AGENTS.md`. A relative import
resolves against the file containing it, which is a symlink into this repo — so
a relative path would be ambiguous. Note that importing does not save context:
imported files load at launch regardless.

## settings.json vs settings.local.json

Claude Code writes machine-local permission grants into `settings.local.json`.
That file is gitignored and never linked — keep the durable, portable rules in
`settings.json` here and let the local file stay local.

## Not linked

`.credentials.json`, `history.jsonl`, `projects/`, `todos/`, and `statsig/` are
runtime state. `plugins/` is managed by Claude Code's own plugin installer; track
plugin *sources* in `settings.json` rather than linking the installed tree.
