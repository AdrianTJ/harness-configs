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

`attribution.pr` and `attribution.commit` are both blanked so Claude Code stops
appending its "Generated with Claude Code" footer to pull request bodies and
commit messages.

This only governs what Claude Code appends on its own. The `Co-Authored-By`
trailer convention in `CLAUDE.md` is unaffected — that trailer is passed
explicitly in the commit command, not auto-appended.

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

## Hooks

The `SessionStart` hook reports the session to the herdr app. Only the settings
line is tracked here; the script itself (`~/.claude/hooks/herdr-agent-state.sh`)
is herdr-managed, regenerates on reinstall, and is never linked or committed.
It exits silently when herdr isn't running, so the line is harmless on machines
without it.

The command is written in `$HOME` form so it works on any machine. herdr's
installer writes an absolute path — if a reinstall rewrites the line that way,
re-apply the portable form when the diff shows up.

### Orca agent-hooks

The Orca terminal injects its own cross-platform agent hooks into
`SessionStart`, `PreToolUse`, and `UserPromptSubmit` on launch, including a
generated PowerShell fallback for Windows. Because this repo links
`settings.json`, that shows up as an uncommitted `git status` change here.
Treat it as known app-managed drift: leave it uncommitted, don't revert it from
the repo side (that would strip the hooks from the live config), and re-apply
the herdr and git-guardrails lines by hand if an Orca update ever clobbers
them.

## Permissions

`skipDangerousModePermissionPrompt` is set, so dangerous-mode runs don't prompt.
Delete the line if you want the prompt back.

## Not linked

`.credentials.json`, `history.jsonl`, `projects/`, `todos/`, and `statsig/` are
runtime state. `plugins/` is managed by Claude Code's own plugin installer; track
plugin *sources* in `settings.json` rather than linking the installed tree.
