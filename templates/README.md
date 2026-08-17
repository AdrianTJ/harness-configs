# templates/

Starting points to **copy** into a new project. Unlike everything else in this
repo, these are not symlinked — a project's config should be committed to that
project and free to diverge, not silently changed when you edit this repo.

`install.sh` ignores this directory entirely.

```sh
# drop the default template into a project
cp -R ~/harness-configs/templates/default/. /path/to/project/
```

## default/

The baseline: an `AGENTS.md` skeleton plus a `CLAUDE.md` that points at it, so a
project has one instruction file no matter which harness opens it.

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
