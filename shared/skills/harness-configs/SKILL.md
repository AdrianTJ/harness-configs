---
name: harness-configs
description: Install, sync, update, or repair the user's agent harness configs (pi, Claude Code, codex, opencode, herdr) from their harness-configs repo. Use when asked to set up harness configuration on a machine, deploy or re-link configs, add a config file to the repo, check whether configs are correctly linked, or undo the linking. Also use when a harness config file appears to be a symlink and the user wants to change it.
---

# harness-configs

The user keeps every harness's configuration in one git repo and symlinks it into
each harness's real config directory. Config files under `~/.pi/agent/`,
`~/.claude/`, `~/.codex/`, `~/.config/opencode/`, and `~/.config/herdr/` are
therefore **symlinks into that repo** — editing them edits the repo, and the
change should be committed.

## Find the repo

If configs are already installed, any linked file points back to it:

```sh
for probe in ~/.claude/CLAUDE.md ~/.pi/agent/AGENTS.md ~/.config/herdr/config.toml; do
  [ -L "$probe" ] && { cd "$(dirname "$(readlink "$probe")")"; break; }
done
git rev-parse --show-toplevel
```

If nothing is linked yet, the repo hasn't been deployed on this machine — ask the
user where the clone is, or to clone it.

## Then read its AGENTS.md

The repo root has an `AGENTS.md` that is the authoritative runbook: preflight,
install order, per-harness post-link steps, verification, and the rules about
credentials. **Read it and follow it** rather than working from this summary.

The short version, for orientation only:

```sh
./install.sh --dry-run     # preview, writes nothing
./install.sh               # link everything
./install.sh --harness pi  # limit to one harness
./install.sh --status      # what's linked, missing, or in the way
./install.sh --unlink      # remove only symlinks pointing into the repo
```

## Two things that are easy to get wrong

**Changing a harness config means editing the repo and committing.** A change
made only in `~/.claude/` either edits the repo through the symlink (commit it)
or, if the file isn't linked, will be overwritten as a `.bak-*` backup on the
next install. Check with `ls -l` whether you're looking at a symlink.

**Adding a config file requires a manifest line.** `links.conf` declares every
symlink; `install.sh` does nothing that isn't declared there. A new file in a
harness folder does nothing until its manifest line exists.

**A skill from outside this repo needs a source entry.** `SOURCES.md` at the
repo root is the ledger of upstream sources, pinned revisions, and refresh
procedures for every vendored or referenced skill. Check it (and the skill's
attribution footer) before updating a skill, and add an entry when vendoring a
new one.

Never commit credentials. `auth.json`, `models.json`, `.credentials.json`,
`settings.local.json`, and session files are deliberately unlinked and gitignored.
