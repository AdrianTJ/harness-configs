# harness-configs

Configuration for the agent harnesses I use, in one repo, symlinked into place.

```
harness-configs/
├── install.sh       symlink manager
├── links.conf       the manifest install.sh reads, the source of truth
├── AGENTS.md        runbook for an agent installing this (CLAUDE.md imports it)
├── scripts/         repo checks: manifest, settings, skills
├── shared/
│   ├── AGENTS.md      global instructions, deployed to every harness
│   └── skills/        Agent Skills, deployed to pi and Claude Code
├── pi/              → ~/.pi/agent/
└── claude-code/     → ~/.claude/  (CLAUDE.md only)
```

codex gets `shared/AGENTS.md` and nothing else.

## Install

```sh
./install.sh --dry-run     # see exactly what would happen
./install.sh               # link it all
./install.sh --harness pi  # just one harness
./install.sh --status      # what's linked, what's missing, what's in the way
./install.sh --unlink      # remove only the symlinks this repo created
```

Nothing outside `links.conf` is ever touched. A real file already at a target path is moved to `<name>.bak-<timestamp>` before the symlink replaces it, so a first run on a populated machine is recoverable. Entries whose source doesn't exist are skipped.

## What is deliberately not tracked

Every harness keeps credentials and state next to its config, so the manifest links individual files and directories, never whole config roots:

- pi: `sessions/`, `trust.json`, `auth.json`, `models.json`, `git/`, `npm/`
- Claude Code: `settings.json`, `.credentials.json`, `history.jsonl`, `projects/`, `settings.local.json`
- codex: everything but `AGENTS.md`

## Adding something new

1. Put the file in the harness folder, or in `shared/` if a second harness reads the identical format.
2. Add a line to `links.conf`.
3. `./install.sh --dry-run` to check the target, then `./install.sh`.
