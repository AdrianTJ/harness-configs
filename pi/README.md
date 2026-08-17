# pi

Config root: `~/.pi/agent/` (project-level equivalent: `.pi/` in a repo).

| Repo path | Links to | What it is |
|---|---|---|
| `settings.json` | `~/.pi/agent/settings.json` | Global settings: models, providers, defaults. |
| `keybindings.json` | `~/.pi/agent/keybindings.json` | Key overrides. |
| `APPEND_SYSTEM.md` | `~/.pi/agent/APPEND_SYSTEM.md` | Appended to the system prompt. (`SYSTEM.md` *replaces* it — use with care.) |
| `extensions/` | `~/.pi/agent/extensions/` | TypeScript extensions: tools, commands, hooks, UI. |
| `themes/` | `~/.pi/agent/themes/` | Custom themes, hot-reloaded. |
| `skills/` | `~/.pi/agent/skills/` | pi-only skills. Portable ones go in `shared/skills/`. |
| `prompts/` | `~/.pi/agent/prompts/` | pi-only prompt templates. Portable ones go in `shared/prompts/`. |

`AGENTS.md` is linked from `shared/AGENTS.md`, not stored here.

## Extensions

pi ships without MCP, subagents, or plan mode by design and expects you to add
what you want. Two ways to track an extension here, and the choice matters:

**Vendored** — the extension source lives in `extensions/<name>/` and is
committed. Good for extensions you wrote or modified. `node_modules/` is
gitignored, so a fresh machine needs `npm install` in each extension directory
after linking.

**Declared** — the extension is installed by pi itself (`pi install npm:<pkg>`)
into `~/.pi/agent/npm/`, which this repo deliberately does not link or track.
Record it in `extensions.txt` instead so a new machine can replay the list.
Better for third-party extensions you don't patch — no vendored copies to keep
up to date.

Your `fff` and subagents extensions can go either way; declared is usually the
lower-maintenance option unless you're carrying local changes.

## Not linked

`sessions/`, `trust.json`, `git/`, and `npm/` are pi's own state. Leave them
alone — linking them would drag session logs and installed packages into git.
