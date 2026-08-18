# harness-configs

Configuration for every agent harness I use, in one repo, symlinked into place.

One folder per harness, mirroring that harness's real config directory, plus a
`shared/` folder for the config that more than one harness consumes verbatim.

```
harness-configs/
├── install.sh          symlink manager
├── links.conf          the manifest install.sh reads — the source of truth
├── SOURCES.md          the ledger of where vendored skills are fetched from
│
├── AGENTS.md           runbook for an agent installing this (CLAUDE.md imports it)
│
├── shared/             consumed by more than one harness, no translation needed
│   ├── AGENTS.md         global instructions (Claude Code reads it as CLAUDE.md)
│   ├── skills/           Agent Skills standard — pi and Claude Code both take these
│   └── prompts/          portable prompt templates
│
├── pi/                 → ~/.pi/agent/
├── claude-code/        → ~/.claude/
├── codex/              → ~/.codex/
├── opencode/           → $XDG_CONFIG_HOME/opencode/
├── herdr/              → $XDG_CONFIG_HOME/herdr/
│
└── templates/          copied into new projects, never linked
```

Each harness folder has its own README with the exact path mapping and the
harness-specific gotchas.

Agents get their own runbook: [`AGENTS.md`](AGENTS.md) at the repo root has the
ordered install procedure, per-harness post-link steps, and the credential rules.
Any harness that opens this repo reads it automatically. The same guidance ships
as the `harness-configs` skill in `shared/skills/` for use from other machines
and other repos, once configs are installed.

## Install

```sh
./install.sh --dry-run     # see exactly what would happen
./install.sh               # link it all
./install.sh --harness pi  # just one harness
./install.sh --status      # what's linked, what's missing, what's in the way
./install.sh --unlink      # remove only the symlinks this repo created
```

Nothing outside `links.conf` is ever touched. A real file already sitting at a
target path is moved to `<name>.bak-<timestamp>` before the symlink replaces it,
so a first run on a populated machine is recoverable.

Entries whose source doesn't exist yet are skipped rather than failing, so the
manifest can describe the full intended surface while you fill it in.

## herdr writes into the others

herdr is not just a sixth folder. `herdr integration install <agent>` installs
hooks into pi's, Claude Code's, codex's, and opencode's own config directories —
the ones this repo symlinks. So those hooks land in tracked files and version
themselves for free.

The ordering matters: **link first, integrate second.** Run `./install.sh`, then
`herdr integration install <agent>`, then commit the diff. Do it the other way
round and the hooks go into real files that `install.sh` will later move aside as
`.bak-*` backups.

## How the sharing works

The harnesses have converged more than their docs suggest, which is what makes
a `shared/` folder worth having:

| | pi | Claude Code | codex | opencode |
|---|---|---|---|---|
| Instructions file | `AGENTS.md` | `CLAUDE.md` | `AGENTS.md` | `AGENTS.md` |
| Skills (`SKILL.md`) | ✓ | ✓ | — | — |
| Prompt templates | `prompts/` | `commands/` | `prompts/` | `command/` |
| Extensions | `extensions/` + `packages[]` | plugins | — | `plugin/` |
| Subagents | via extension | `agents/` | — | `agent/` |

So: **instructions** are one file linked five ways, **skills** are shared
between pi and Claude Code unchanged, and **prompt bodies** are shared where the
frontmatter allows — anything needing harness-specific frontmatter gets a thin
wrapper in that harness's own folder instead.

`merge` entries in the manifest link directory *contents* rather than the
directory itself, which is what lets `shared/skills/` and `pi/skills/` both feed
`~/.pi/agent/skills/` without either one shadowing the other.

## What is deliberately not tracked

Every harness keeps credentials and state next to its config. None of it is
linked or committed:

- pi: `sessions/`, `trust.json`, `auth.json`, `models.json`, `git/`, `npm/`
- Claude Code: `.credentials.json`, `history.jsonl`, `projects/`, `settings.local.json`
- codex: `auth.json`, `sessions/`
- herdr: `session.json`, `herdr.log`, `plugins/`, and `~/.herdr/worktrees/`

This is why the manifest links individual files and subdirectories rather than
whole config roots. Linking `~/.claude` or `~/.pi/agent` wholesale would pull
credentials into git the first time the harness wrote to them.

## Adding something new

1. Put the file in the harness folder — or in `shared/` if a second harness
   reads the identical format.
2. Add a line to `links.conf`.
3. `./install.sh --dry-run` to check the target, then `./install.sh`.
