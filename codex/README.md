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

## config.toml

`~/.codex/config.toml` on a machine with the ChatGPT desktop app is owned by
that app: marketplaces, versioned plugin paths, injected MCP servers, and
per-project trust entries. Vendoring it would churn on every app update — and
replacing the live file would break the app — so `codex/config.toml` stays
unpopulated here until there is a standalone-CLI machine to author a minimal
portable config for (model, approval mode, sandbox).
