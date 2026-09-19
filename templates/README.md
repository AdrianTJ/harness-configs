# templates/

Starting points to **copy** into a new project. Unlike everything else in this
repo, these are not symlinked — a project's config should be committed to that
project and free to diverge, not silently changed when you edit this repo.

`install.sh` ignores this directory entirely.

```sh
# drop the default template into a project (from the repo root)
cp -R templates/default/. /path/to/project/
```

## default/

The baseline: a single `AGENTS.md` skeleton. Every harness reads it natively —
Claude Code included, since v2.1.277 added AGENTS.md project-instruction support
(no `CLAUDE.md` shim needed anymore; Claude Code skips it when sessions run on
Bedrock or third-party providers, in which case add a one-line `@AGENTS.md`
import file back).

Add more templates as siblings (`templates/rust/`, `templates/monorepo/`, …)
when a project type earns its own starting point.

## What belongs in a project template

Project-scoped equivalents of the global config: `.pi/settings.json`,
`.claude/settings.json`, `AGENTS.md`, project skills under `.claude/skills/` or
`.pi/skills/`. Keep them thin — they layer on top of the global config, they
don't replace it.

Note that pi requires a trust decision before it loads `.pi/settings.json` and
project extensions, so a freshly copied template won't take effect until you
accept the prompt in that directory.
