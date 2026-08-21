# herdr

Config root: `$XDG_CONFIG_HOME/herdr/` (usually `~/.config/herdr/`), confirmed by
the header of `herdr --default-config`.

herdr is the odd one out in this repo, in two ways. It's a multiplexer that
*runs* the other harnesses rather than prompting a model itself, so its config is
about panes, keys, and agent-state UI. And it's the only harness here that
**writes into the other harnesses' config directories** — see Integrations below.

| Repo path | Links to | What it is |
|---|---|---|
| `config.toml` | `.../herdr/config.toml` | Everything: theme, keys, UI, sound, session, remote. One monolithic file — no include mechanism. |
| `scripts/` | `.../herdr/scripts/` | Helper scripts invoked by `[[keys.command]]` bindings. |
| `sounds/` | `.../herdr/sounds/` | `.mp3` files for `[ui.sound]` notifications. |

## config.toml

Checked in as the full commented output of `herdr --default-config`, with every
setting left at its default. That's deliberate: because the baseline is pure
defaults, `git diff` shows exactly which knobs you've actually turned, and the
inline documentation for every neighbouring option stays at hand while you edit.

Regenerate the baseline after a herdr upgrade to pick up new options:

```sh
herdr --default-config > /tmp/herdr-new.toml
diff /tmp/herdr-new.toml herdr/config.toml   # review, then merge by hand
```

`prefix+shift+r` reloads the config without restarting, so editing the file in
this repo and hitting reload is a tight loop.

## Relative paths and the symlink

`[ui.sound]` documents that "relative paths are resolved from this config file's
directory". Since `~/.config/herdr/config.toml` is a symlink into this repo,
"this config file's directory" is ambiguous — it depends on whether herdr
canonicalises the path before taking its parent.

`scripts/` and `sounds/` are therefore linked into `~/.config/herdr/` as well as
living here, so `sounds/notification.mp3` resolves either way. If you'd rather
not rely on that, use absolute paths in `config.toml` instead.

## Integrations — this is the interesting one

`herdr integration install <agent>` installs hooks into the *agent's own* config
directory, for pi, claude, codex, opencode, and others. That's what lets herdr
report accurate agent state and resume sessions
(`[session] resume_agents_on_restore`).

Where those hooks land depends on what herdr writes. An edit to a file this repo
already links — `claude-code/settings.json`, `pi/settings.json` — goes through
the symlink and shows up as a normal diff. But a *new* file written into a
directory linked with `merge` does not: `merge` links a directory's contents, so
an empty repo-side directory means nothing is linked and the target is a plain
directory. The file lands there untracked.

That is what happens with pi. `herdr integration install pi` writes
`~/.pi/agent/extensions/herdr-agent-state.ts`, and `pi/extensions/` starts empty,
so the hook is invisible to `git status`. Move it into `pi/extensions/` and
re-run `./install.sh --harness pi` to capture it.

**Run `install.sh` first, then the integrations.** In that order the hooks are
captured in git and deploy to every machine automatically. In the other order
they get written to real files that `install.sh` will later move aside as
`.bak-*` backups, and you'll wonder where your integration went.

After running an integration, `git diff` and commit the hook it added.

## Plugins

herdr installs plugins into `~/.config/herdr/plugins/`. That directory is
**neither linked nor tracked** — it's an installed artifact, the same call made
for pi's `npm/` and `git/` package directories.

Record what you install in `plugins.txt` so a new machine can be rebuilt, and
keep any hand-written glue (an editor-side script a plugin needs, for example)
in `scripts/` where it *is* tracked.

## Agent IDs

herdr's canonical agent IDs — used by `[ui.sidebar.agents.rows_by_agent]`,
`[ui.sound.agents]`, and `[experimental] cjk_ime_agents` — cover four of the five
harnesses in this repo: `pi`, `claude`, `codex`, `opencode`. Note it's `claude`,
not `claude-code` as this repo's folder is named.

## Not linked

`session.json`, `herdr.log`, the server socket, and `plugins/` are runtime state.
Worktrees created with `prefix+shift+g` default to `~/.herdr/worktrees` — a
different directory from the config root, holding real git checkouts. Never
track either.
