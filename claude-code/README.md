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

## Attribution

`attribution.pr` is blanked so Claude Code stops appending a "Generated with
Claude Code" footer to pull request bodies.

`attribution.commit` is deliberately left unset. It governs the
`Co-Authored-By: Claude` trailer, which the git convention in `CLAUDE.md`
*wants* on commits — blanking it would remove the credit line, not just the
marketing one. Set `"commit": ""` only if you change that convention.

The older `includeCoAuthoredBy` setting is deprecated in favour of this one, and
the two conflict if both are set. Use `attribution` alone.

Two caveats worth knowing:

- The setting needs Claude Code v2.0.62 or later, and there is an open report
  (anthropics/claude-code#18253) of it not being honoured in some versions. If a
  footer still appears, that is the bug, not a misconfiguration.
- It governs Claude Code the CLI. Pull requests opened from a Claude Code *web
  or remote* session go through a server-side GitHub integration that appends
  its own footer, which a repo-level setting does not reach. For those, the
  reliable answer is to have the agent push the branch and open the PR yourself.

## settings.json vs settings.local.json

Claude Code writes machine-local permission grants into `settings.local.json`.
That file is gitignored and never linked — keep the durable, portable rules in
`settings.json` here and let the local file stay local.

## Not linked

`.credentials.json`, `history.jsonl`, `projects/`, `todos/`, and `statsig/` are
runtime state. `plugins/` is managed by Claude Code's own plugin installer; track
plugin *sources* in `settings.json` rather than linking the installed tree.
