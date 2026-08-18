# pi

Config root: `~/.pi/agent/` (project-level equivalent: `.pi/` in a repo).

| Repo path | Links to | What it is |
|---|---|---|
| `settings.json` | `~/.pi/agent/settings.json` | All settings, including the `packages` list below. |
| `keybindings.json` | `~/.pi/agent/keybindings.json` | Key overrides. |
| `APPEND_SYSTEM.md` | `~/.pi/agent/APPEND_SYSTEM.md` | Appended to the system prompt. (`SYSTEM.md` *replaces* it — use with care.) |
| `extensions/` | `~/.pi/agent/extensions/` | Locally-authored extensions, auto-discovered as `*.ts` or `*/index.ts`. |
| `themes/` | `~/.pi/agent/themes/` | Custom themes, hot-reloaded. |
| `skills/` | `~/.pi/agent/skills/` | pi-only skills. Portable ones go in `shared/skills/`. |
| `prompts/` | `~/.pi/agent/prompts/` | pi-only prompt templates. Portable ones go in `shared/prompts/`. |

`AGENTS.md` is linked from `shared/AGENTS.md`, not stored here.

## Packages are declared, not vendored

pi has a native mechanism for this, so there's no separate ledger file: the
`packages` array in `settings.json` *is* the list, and `pi install` writes to it.
Since `settings.json` is tracked here, installing a package on one machine
commits it for all of them.

```sh
pi install npm:some-extension   # adds to packages[] and downloads
pi list                         # what's declared
pi update --extensions          # update all packages, reconcile pinned git refs
pi remove npm:some-extension    # drop it
```

The downloaded code lands in `~/.pi/agent/npm/` and `~/.pi/agent/git/`, which are
deliberately **not** linked or tracked — same call as herdr's `plugins/`. Only the
declaration is version-controlled; the bytes are re-fetched per machine.

Specs accept `npm:pkg`, `npm:@scope/pkg@1.2.3`, `git:github.com/user/repo@v1`, and
absolute local paths. A spec carrying an explicit version is pinned and skipped by
`pi update`, so these are intentionally left unpinned — this ecosystem moves fast
(pi-btw shipped v0.52 within days of writing) and pinning would silently freeze
them. Pin any package you need to hold still.

## The installed set

| Package | What it gives you |
|---|---|
| `npm:@bacnh85/pi-fff` | FFF-powered fuzzy file and content search. |
| `npm:@jqwn/pi-ask-user-question` | `ask_user_question` — multi-question TUI dialogs with options, descriptions, and previews, so the model asks instead of guessing. |
| `npm:@narumitw/pi-btw` | `/btw` side-question thread, answered in an ephemeral UI without polluting the main conversation. |
| `npm:@dietrichgebert/ponytail` | "Lazy senior dev" mode — YAGNI ladder, stdlib-first, shortest diff. Ships an extension *and* skills. |
| `npm:pi-subagents` | Delegation to child agents, foreground or background. pi ships without subagents by design; this adds them. |
| `npm:pi-tasks` | Evidence-gated task plans that survive compaction and crashes, resumable via `/task-resume`. |
| `npm:pi-web-access` | Web search and fetch, plus GitHub clone, PDF extraction, and YouTube. Defaults to Exa with no API key. |

Which of these ship skills (ponytail and pi-subagents do; the rest are
extensions only) is recorded in `SOURCES.md` under "pi package skills" — check
there before assuming a package's skills are accounted for.

Two are worth knowing more about:

**ponytail is cross-harness.** The same npm package carries a `pi` manifest key
(extension + skills) and an `.opencode/` plugin. So when you set up opencode, it's
the same package declared a second way — not a second tool to learn.

**pi-web-access needs no key by default.** It works out of the box through Exa.
If you later switch it to Brave, Tavily, or Parallel, those keys belong in the
environment or `auth.json`, never in `settings.json` — that file is tracked.

## First run on a new machine

```sh
./install.sh --harness pi   # link settings.json and friends
pi                          # installs missing packages from packages[]
/login                      # or set a provider API key
```

Auth is *not* handled here by design: pi writes credentials to
`~/.pi/agent/auth.json` at `0600`, which is neither linked nor tracked.

## Local extensions vs packages

`extensions/` is for extensions you write yourself — pi auto-discovers `*.ts` and
`*/index.ts` there, and since the directory is linked, the source is tracked. Use
it for glue too small or too personal to publish. Anything from npm or git belongs
in `packages` instead.

## Not linked

`sessions/`, `trust.json`, `auth.json`, `models.json` (which can carry custom
provider keys), and the `npm/` and `git/` package trees are pi's own state.
