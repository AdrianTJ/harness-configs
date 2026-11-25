# pi

Config root: `~/.pi/agent/` (project-level equivalent: `.pi/` in a repo).

| Repo path | Links to | What it is |
|---|---|---|
| `settings.json` | `~/.pi/agent/settings.json` | Model, thinking level, theme, and the `packages` list. |
| `agents/` | `~/.pi/agent/agents/` | Subagent definitions for pi-subagents (`researcher`). |

`AGENTS.md` is linked from `shared/AGENTS.md`, and shared skills are merged into `~/.pi/agent/skills/`.

The default model is Anthropic's `claude-haiku-5-5` with thinking `high`, so pi needs an Anthropic login (`/login`) or `ANTHROPIC_API_KEY` on each machine.

## Packages are declared, not vendored

The `packages` array in `settings.json` is the list, and `pi install` writes to it. Since `settings.json` is tracked, installing a package on one machine commits it for all of them.

```sh
pi install npm:some-extension   # adds to packages[] and downloads
pi list                         # what's declared
pi update --extensions          # update downloaded packages
pi remove npm:some-extension    # drop it
```

`pi update --extensions` never fetches a declared-but-never-downloaded spec, even though it reports "Updated packages". On a fresh machine, run `pi install` for each spec in `settings.json` first; re-running it on an already-declared spec is safe.

The downloaded code lands in `~/.pi/agent/npm/` and `~/.pi/agent/git/`, which are not linked or tracked. Specs are left unpinned so `pi update` keeps them current; add a version (`npm:pkg@1.2.3`) to hold one still.

## The installed set

| Package | What it gives you |
|---|---|
| `npm:@bacnh85/pi-fff` | Fuzzy file and content search. |
| `npm:@jqwn/pi-ask-user-question` | `ask_user_question` dialogs, so the model asks instead of guessing. |
| `npm:@narumitw/pi-btw` | `/btw` side-question thread that stays out of the main conversation. |
| `npm:pi-subagents` | Subagent delegation: foreground and background runs, worktrees. |
| `npm:pi-tasks` | Task plans that survive compaction and crashes, resumable via `/task-resume`. |
| `npm:pi-web-access` | Web search and page fetch. Keyless by default; optional provider keys go in `~/.pi/agent/web-search.json`, never in `settings.json`. |

`agents/researcher.md` loads pi-web-access into its child sessions by path, so keep that package if you keep the researcher.

## First run on a new machine

```sh
./install.sh --harness pi   # link settings.json, AGENTS.md, agents, skills
pi install <spec>           # for each package pi list is missing
pi                          # then /login
```

## Not linked

`sessions/`, `trust.json`, `auth.json`, `models.json`, `extensions/`, and the `npm/` and `git/` package trees are pi's own state. Apps that install pi extensions (Orca, herdr) write into `~/.pi/agent/extensions/`; leave those untracked.
