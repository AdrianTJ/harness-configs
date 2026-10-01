# Claude Code

Config root: `~/.claude/` (project-level equivalent: `.claude/` in a repo).

| Repo path | Links to | What it is |
|---|---|---|
| `settings.json` | `~/.claude/settings.json` | Permissions, hooks, env, model. |
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | Imports the shared instructions, then adds Claude-only rules. |
| `agents/` | `~/.claude/agents/` | Subagent definitions (markdown + frontmatter). |
| `commands/` | `~/.claude/commands/` | Slash commands. |
| `hooks/` | `~/.claude/hooks/` | Hook scripts invoked by `settings.json` (merge-linked, so foreign scripts can sit beside them). |
| `skills/` | `~/.claude/skills/` | Claude-Code-only skills; portable ones come from `shared/skills/`. |

`CLAUDE.md` here is a real file, not a symlink. It imports `shared/AGENTS.md`
(linked alongside it as `~/.claude/AGENTS.md`) and then adds the rules that only
apply to Claude Code. The import is still the only path to the shared
instructions: AGENTS.md support added in Claude Code v2.1.277 is a *project*
fallback (used when a repo has no CLAUDE.md), and the user-level
`~/.claude/CLAUDE.md` always loads without triggering that fallback.

The import is written as an absolute `@~/.claude/AGENTS.md`. A relative import
resolves against the file containing it, which is a symlink into this repo — so
a relative path would be ambiguous. Note that importing does not save context:
imported files load at launch regardless.

## AGENTS.md support (v2.1.277+)

Claude Code reads a repository's `AGENTS.md` natively when the project has no
`CLAUDE.md`/`CLAUDE.local.md` in the working directory or above it, so new
projects no longer need a `CLAUDE.md` shim — see `templates/default/`.
Behaviour is configurable via `/config` → "Project instructions" (four modes,
including loading both formats); the setting lives in user or managed settings,
never a repo's `.claude/settings.json`. Support is unavailable on Bedrock,
Vertex, third-party providers, or with telemetry disabled, and does not extend
to `.agents/skills` — skills remain per-harness.

Project files that already import AGENTS.md (like this `CLAUDE.md`) are safe to
keep in either mode: Claude Code never reads an AGENTS.md twice.

## Attribution

`attribution.pr` and `attribution.commit` are both blanked so Claude Code stops
appending its "Generated with Claude Code" footer to pull request bodies and
commit messages.

This only governs what Claude Code appends on its own. Commits carry no
`Co-Authored-By` trailer at all — see the Git section of `CLAUDE.md`.

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

`block-dangerous-git.sh` (PreToolUse/Bash) is a personal guardrail, tracked
here and merge-linked so it deploys with the rest of the config. It needs
`jq`; without it the script exits 0 and the guardrail fails open, so keep
jq installed.

### Tool-injected hooks stay out

Terminal apps and agent managers (the ones you try out, not your primary tools)
rewrite `~/.claude/settings.json` on launch to add their own hooks and status
line. Because this repo links that file, the injection shows up as a `git diff`
here, and once a commit swallowed ~30 KB of it. The only hook tracked is
`block-dangerous-git.sh`. `scripts/check-settings.py` (part of `check.sh`, so the
pre-push hook and CI) fails on a hook that calls a script not tracked in
`hooks/`, on a `statusLine`, on a settings file over 8 KB, and on known app names.

If an app rewrites the file, discard its changes with
`git checkout claude-code/settings.json`; the app re-adds its hooks to the live
config next launch, which is the app's business, not this repo's.

## Permissions

`skipDangerousModePermissionPrompt` is set, so dangerous-mode runs don't prompt.
Delete the line if you want the prompt back.

## Not linked

`.credentials.json`, `history.jsonl`, `projects/`, `todos/`, and `statsig/` are
runtime state. `plugins/` is managed by Claude Code's own plugin installer; track
plugin *sources* in `settings.json` rather than linking the installed tree.
