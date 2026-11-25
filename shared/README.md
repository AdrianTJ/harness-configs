# shared/

Config that more than one harness reads in the same format.

| Path | Consumed by |
|---|---|
| `AGENTS.md` | pi and codex (as `AGENTS.md`); Claude Code (imported by `claude-code/CLAUDE.md`) |
| `skills/` | pi (`~/.pi/agent/skills`), Claude Code (`~/.claude/skills`) |

Keep `AGENTS.md` harness-neutral and short.

## Skills

One directory per skill, each with a `SKILL.md` whose frontmatter has `name` (matching the directory) and `description`. A skill may also set `disable-model-invocation: true` to make it user-invoked only. `scripts/validate-skills.py` and `scripts/check-skill-refs.sh` check this in CI.

Current set: `harness-configs`, `log-decision`, `sync-docs`, `write-skill`, all written for this repo. Upstream skills that need no adaptation are installed per machine with `npx skills add`, not vendored here.
