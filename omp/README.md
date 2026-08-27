# omp

Config root: `~/.omp/agent/`. OMP is a pi fork, so the layout mirrors `pi/` —
the main difference is that settings live in `config.yml` instead of
`settings.json`.

| Repo path | Links to | What it is |
|---|---|---|
| `config.yml` | `~/.omp/agent/config.yml` | Model roles (default/smol/slow/plan), theme, composer shape. |
| `extensions/` | `~/.omp/agent/extensions/` | Auto-discovered `*.ts` extensions, same API as pi's. |

`AGENTS.md` is linked from `shared/AGENTS.md`, and `shared/skills/` merges into
`~/.omp/agent/skills/`, both same as pi.

## Not linked

`agent.db`, `history.db`, `models.db` (and their `-shm`/`-wal` companions),
`sessions/`, `terminal-sessions/`, `blobs/`, `cache/`, and `config.yml.lock`
are OMP's own state. The `~/.omp/` root above `agent/` (autoqa.db, gpu_cache,
puppeteer, natives, logs) is app state, never linked.

## Gotchas

- Model refs carry a provider prefix like pi's, e.g.
  `opencode-go/glm-5.3-flash:high` — the `:high` suffix is the thinking level.
- OMP reads pi's `PI_SMOL_MODEL` / `PI_SLOW_MODEL` / `PI_PLAN_MODEL` env vars
  for its model roles.
- `~/.omp/agent/extensions/` may hold Orca-managed `orca-*.ts` files as real
  files (not symlinks) when the Orca app is installed. Whether to capture
  those is an open decision — they are Orca's to rewrite, so tracking them
  means committing Orca's updates as they land.
