# opencode

Config root: `$XDG_CONFIG_HOME/opencode/` (usually `~/.config/opencode/`).

| Repo path | Links to | What it is |
|---|---|---|
| `opencode.json` | `.../opencode/opencode.json` | Providers, models, MCP servers, permissions, theme. |
| `tui.jsonc` | `.../opencode/tui.jsonc` | TUI plugin list, written by `herdr integration install opencode`. |
| `herdr-tui-session.js` | `.../opencode/herdr-tui-session.js` | herdr's TUI session plugin, managed by herdr — reinstalls update it through the symlink. |
| `agent/` | `.../opencode/agent/` | Agent definitions (note: singular `agent`, not `agents`). |
| `command/` | `.../opencode/command/` | Custom commands (singular `command`). |
| `plugin/` | `.../opencode/plugins/` | JS/TS plugins (repo folder is singular, opencode's target directory is plural). |

`AGENTS.md` is linked from `shared/AGENTS.md`.

The singular directory names are the easiest thing to get wrong here — opencode
uses `agent/`, `command/`, and `plugin/` where Claude Code uses `agents/` and
`commands/`.

Commands are not shared from `shared/prompts/` because opencode expects its own
frontmatter. If you want to reuse a shared prompt body, add a thin wrapper file
under `command/` here.
