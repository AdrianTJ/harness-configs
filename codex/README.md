# codex

Config root: `~/.codex/`.

| Repo path | Links to | What it is |
|---|---|---|
| `config.toml` | `~/.codex/config.toml` | Model, provider, approval mode, sandbox settings. |
| `prompts/` | `~/.codex/prompts/` | Codex-only prompt templates, expanded as `/name`. |

`AGENTS.md` is linked from `shared/AGENTS.md`; portable prompts come from
`shared/prompts/`.

## Not linked

`auth.json` holds credentials. `sessions/` and `log/` are runtime state.
