# Dogfooding vendor tools: skills CLI (Vercel) and dotagents (Sentry)

Branch `dogfood-vendors`. Question: should this repo adopt out-of-the-box tooling
for managing agent configs and skills, or keep building the thin layer it has
(`links.conf` + `install.sh` + `SOURCES.md`)?

Both tools were tested on this machine, in a sandbox first and then against the
real harnesses (`pi`, `claude`, `opencode`; `codex` not installed). Everything
was removed afterwards — the machine is back to baseline.

## Tested surface

| Capability | Our repo | skills CLI 1.5.22 (Vercel) | dotagents 3.0.1 (Sentry) |
|---|---|---|---|
| Symlink fan-out into `~/.pi/agent/skills`, `~/.claude/skills` | `install.sh` + `links.conf` | automatic, relative symlinks | none — no fan-out at all |
| opencode / universal discovery | manual links | `~/.agents/skills` (opencode reads it natively) | `~/.agents/skills` (same) |
| Version pinning | `SOURCES.md` (manual, commit pins) | `.skill-lock.json` v3, GitHub tree SHA, `check`/`update` | `agents.lock` with `resolved_commit` per source, auto-pinned on `add` |
| Update / drift detection | manual | `skills check -g` works (verified) | `install`/`update` against lock |
| Preflight: skip absent harnesses | yes | yes — did not create `~/.codex` | n/a (no fan-out) |
| Security | reviewed by hand | install-time warning banner | `trust` policy, `warden.toml`, `minimum_release_age` |
| Prompt-only use (no install) | n/a | `skills use <src>@<skill>` (works) | n/a |
| Company backing | — | Vercel | Sentry |
| herdr support | yes | no | no |
| pi package management (`settings.json` packages) | yes | no | no |

## skills CLI (Vercel) — findings

- **Global install works end to end.** `skills add <repo> --skill <name> -g -a pi -a claude-code -a opencode`:
  - materializes the skill into `~/.agents/skills/<name>/` (the ecosystem store),
  - symlinks `~/.pi/agent/skills/<name>` and `~/.claude/skills/<name>` with
    **computed relative** symlinks,
  - leaves opencode to read `~/.agents` natively — verified with
    `opencode debug skill`, which lists the skill at its `~/.agents` path.
- **Remove is clean.** `skills remove` deletes store entry and both symlinks;
  opencode stops seeing the skill immediately.
- **`skills use` works** — generates a ready-to-pipe prompt embedding the
  SKILL.md, no install needed.
- **Update tracking works** (verified against source and in practice):
  `.skill-lock.json` v3 records the GitHub tree SHA of the skill folder;
  `skills check -g` compares against GitHub. On this machine the lock lands at
  `$XDG_STATE_HOME/skills/.skill-lock.json`.
- **Machine-specific hazard: `XDG_STATE_HOME` is hijacked.** The opencode
  desktop app exports `XDG_STATE_HOME=/Users/ryo/Library/Application Support/ai.opencode.desktop`,
  so the skills CLI's global lock (and any other XDG-state tool) writes into
  the desktop app's support directory. Functional today, but the state dies if
  that app is ever uninstalled, and it pollutes an Electron app's dir. Not the
  CLI's bug — the CLI follows the spec. Worth fixing at the env level.
- **Project scope** installs copy into `./.agents/skills/` and write a
  `skills-lock.json` without tree-hash tracking (update checks skip it).
- Wrote nothing into this repo or any tracked file; no credentials touched.

## dotagents (Sentry) — findings

- `init` (global-first) creates `~/.agents/agents.toml` + `agents.lock`.
  `agents.lock` pins `resolved_commit` per source — this automates exactly what
  `SOURCES.md` does by hand.
- `add`/`install`/`list`/`sync`/`doctor` are self-consistent; `doctor` passes.
  Skills land in `~/.agents/skills/` (opencode sees them natively — verified).
- **No fan-out at all.** Nothing was written to `~/.claude/skills` or
  `~/.pi/agent/skills`. Claude Code gets nothing without manually wiring
  marketplace/plugin artifacts; pi only reads plain `skills` entries, and the
  interesting Sentry content ships as **plugins** (`~/.agents/plugins/<name>/`,
  full materialization with `plugin.json`, `.claude-plugin/`, `warden.toml`).
  Plugins are repo-granular: `dotagents add getsentry/skills code-review`
  failed ("plugin not found") — you add the whole repo, not a skill inside it.
- That makes it a team/project-oriented package manager (committed `agents.toml`
  + lock, CI `--frozen`) rather than a personal dotfiles fan-out tool. Its
  self-declared beta status and breaking v0→v1→v3 version churn are real.
- No herdr, no pi packages. Clean removal (`rm -rf ~/.agents`); wrote nothing
  into any repo.

## Verdict: build, but adopt the conventions

Neither tool replaces this repo today:

- **dotagents cannot deliver skills to Claude Code** out of the box on our
  setup, and its plugin model fights the per-skill layout this repo maintains.
- **skills CLI is close** for the skills half (fan-out incl. pi and Claude,
  prompt-use, clean remove, Vercel-backed) but its value is update tracking,
  which on this machine depends on fixing the `XDG_STATE_HOME` pollution first.
- Nothing on the market touches `herdr`, pi's `packages` mechanism, or the
  `install.sh` preflight/backup semantics.

So: keep building the thin layer. But adopt what the ecosystem converged on:

1. **`~/.agents` is real and verified.** opencode reads `~/.agents/skills`
   natively (confirmed via `opencode debug skill`). Treat it as a standard
   location: symlink `shared/skills` into `~/.agents/skills` on install so
   ecosystem tools and opencode share one store.
2. **Skills CLI as the per-machine skill installer** (optional dependency, not
   repo dependency) once `XDG_STATE_HOME` is fixed — it already implements the
   fan-out `install.sh` does for skills, with tree-SHA tracking on top.
3. **Steal `agents.lock`'s shape for `SOURCES.md`**: pin `resolved_commit` per
   source instead of human-remembered SHAs (they're the same data, just
   machine-verifiable).

## Reproduce

```sh
npx skills add vercel-labs/agent-skills --skill web-design-guidelines -g -a pi -a claude-code -a opencode -y
opencode debug skill | grep -A2 web-design-guidelines
npx skills check -g && npx skills remove web-design-guidelines -g -y

npx @sentry/dotagents init
npx @sentry/dotagents add getsentry/skills && npx @sentry/dotagents install
npx @sentry/dotagents doctor && npx @sentry/dotagents list
```