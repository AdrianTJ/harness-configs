# Working in this repo

Runbook for an agent installing these configs on a machine. `shared/AGENTS.md` is a different file: the global instructions that get deployed to the harnesses.

## Install

1. **Preflight.** Check which harnesses exist: `for h in pi claude codex; do printf '%-8s %s\n' "$h" "$(command -v "$h" || echo 'not installed')"; done`. Link only those that are present, and never install a missing harness yourself; tell the user.
2. **Preview, then link.** Run `./install.sh --dry-run` and read it, then `./install.sh --harness pi --harness claude-code` (or whichever are present). Every output line is `linked`, `ok`, `skip` (source not in the repo), or `backup` (a real file moved aside as `.bak-<timestamp>`). For each `backup`, diff it against the linked file and merge anything worth keeping into the repo before it is lost.
3. **pi packages.** `pi list` should show every package in `pi/settings.json`. If any are missing, run `pi install <spec>` for each: `pi update --extensions` silently skips packages that were declared but never downloaded. Then log in with `/login` inside pi; credentials stay in `~/.pi/agent/auth.json`, never tracked.
4. **Verify.** `./install.sh --status` should read `ok` for every populated entry, and `git status --porcelain | grep -Ei 'auth|credential|\.local\.|session' || echo clean` should print `clean`.

## Rules

- `links.conf` is the only place symlinks are declared. Adding a config means a file in the harness folder plus a manifest line.
- Never link a whole config root (`~/.claude`, `~/.pi/agent`): they hold credentials and session state next to config.
- Never commit credentials. If a harness writes a secret into a tracked file, fix the manifest rather than loosening `.gitignore`.
- Run `bash scripts/check.sh` before pushing, or enable the hook once per clone with `git config core.hooksPath .githooks`. CI runs the same script.
- `./install.sh --unlink` removes only symlinks pointing into this repo.
