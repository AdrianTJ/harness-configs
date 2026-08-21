# Working in this repo

Runbook for an agent asked to install these configs on a machine. Read this
before touching anything — the steps have a required order, and getting it wrong
silently discards work.

> **Two files named AGENTS.md.** This one is instructions for working *on* this
> repo, and is never deployed anywhere. `shared/AGENTS.md` is the global
> instruction file that gets *deployed to* the harnesses. Don't edit one meaning
> the other.

## What this repo is

Configs for five agent harnesses, symlinked into their real config directories
from one git repo. One folder per harness mirroring that harness's actual config
layout, plus `shared/` for what more than one harness reads verbatim.

`links.conf` is the manifest and the source of truth: every symlink that gets
made is a line in it. `install.sh` does nothing that isn't declared there.

| Folder | Deploys to | Harness binary |
|---|---|---|
| `pi/` | `~/.pi/agent/` | `pi` |
| `claude-code/` | `~/.claude/` | `claude` |
| `codex/` | `~/.codex/` | `codex` |
| `opencode/` | `$XDG_CONFIG_HOME/opencode/` | `opencode` |
| `herdr/` | `$XDG_CONFIG_HOME/herdr/` | `herdr` |
| `agents/` (store) | `~/.agents/skills/` | none — read natively by opencode (verified); documented alias for Gemini CLI; written by `npx skills` |
| `shared/` | into all of the above | — |
| `templates/` | copied into projects, never linked | — |

## Install

### 1. Preflight

Find out which harnesses are actually present. Only link the ones that are —
linking a harness that isn't installed just creates empty config directories.

```sh
for h in pi claude codex opencode herdr; do
  printf '%-10s %s\n' "$h" "$(command -v "$h" || echo 'not installed')"
done
```

**Do not install missing harnesses.** This repo manages configuration only.
If one the user wants is missing, tell them and let them decide.

The `agents` store is the exception: it has no binary, links unconditionally,
and is safe on any machine.

### 2. Preview, then link

```sh
./install.sh --dry-run              # read this output before proceeding
./install.sh --harness pi --harness claude-code   # ...or whichever are present
```

`--dry-run` writes nothing. Without `--harness` filters, every harness in the
manifest is linked.

Read the output. Every line is one of:

| | Meaning | Action |
|---|---|---|
| `linked` | New symlink created | none |
| `ok` | Already correct | none |
| `skip` | Source not in the repo yet | expected for anything unpopulated |
| `backup` | A real file was moved aside as `.bak-<timestamp>` | see below |
| `conflict` | (status mode) real file in the way | inspect before linking |

**A `backup` line means the machine had a real config there.** Do not ignore it.
Diff the backup against what this repo now links, and if it contained anything
worth keeping, merge it into the repo file and commit — otherwise it's lost the
next time someone cleans up `.bak-*` files.

```sh
diff ~/.pi/agent/settings.json.bak-* ~/.pi/agent/settings.json
```

### 3. Post-link steps, per harness

Linking gets the config files in place. These finish the job:

**pi** — packages are declared in `pi/settings.json` under `packages`, and pi
installs missing ones on startup. Confirm:

```sh
pi list          # should show the seven declared packages
pi update --extensions
```

Auth is separate and never tracked: `/login` inside pi, or a provider API key.
pi writes credentials to `~/.pi/agent/auth.json` at `0600`.

**herdr** — install its integrations, and only after linking:

```sh
herdr integration install pi
herdr integration install claude
herdr integration install codex
herdr integration install opencode
```

These write hooks into the *other* harnesses' config directories. Whether a hook
lands in a tracked file depends on what it writes:

- **Edits to a file this repo already links** (`claude-code/settings.json`, say)
  go through the symlink into the repo, and `git diff` shows them. Commit them.
- **A brand-new file in a directory this repo links with `merge`** does *not*.
  `merge` links a directory's *contents*, so if the repo-side directory is empty,
  nothing is linked and the target stays a real directory. herdr's file lands
  there untracked and `git diff` shows nothing.

The second case is the common one for pi: `herdr integration install pi` writes
`~/.pi/agent/extensions/herdr-agent-state.ts`, and `pi/extensions/` starts empty.

So after running the integrations, check the target directories directly rather
than trusting `git status`:

```sh
ls -la ~/.pi/agent/extensions/ ~/.claude/  # real files here are untracked
```

Move anything real into the matching repo folder, then re-link so it becomes a
tracked symlink:

```sh
mv ~/.pi/agent/extensions/*.ts pi/extensions/
./install.sh --harness pi
git status                                 # now it shows up
```

**claude-code, codex, opencode** — nothing beyond linking, other than auth.

**agents (store)** — the shared skills land in `~/.agents/skills/` via the
manifest. For additional skills that need no adaptation, the ecosystem tool is
the Vercel skills CLI; it writes into the same store and symlinks pi and Claude
Code itself:

```sh
npx skills add <owner>/<repo> --skill <name> -g -a pi -a claude-code -a opencode
npx skills check -g     # drift check against the tree-SHA pin
```

Anything this repo adapts or pins itself goes through `SOURCES.md` instead.
One machine gotcha: the CLI keeps its global state under
`$XDG_STATE_HOME/skills/`, so if the machine exports `XDG_STATE_HOME` into an
app directory, `npx skills update` state dies with the app — fix the env before
relying on it.

### 4. Verify

```sh
./install.sh --status     # every populated entry should read 'ok'
git status                # see what the post-link steps changed
```

Before committing anything the install produced, confirm no credential file got
picked up:

```sh
git status --porcelain | grep -Ei 'auth|credential|\.local\.|session' || echo clean
```

## Order matters in exactly one place

**Link before running herdr integrations.** In that order the hooks herdr writes
land in repo-tracked files and version themselves. In the reverse order they get
written to real files, and the later `install.sh` run moves those aside as
`.bak-*` — the integration appears to have silently vanished.

## Git conventions

Follow these on every commit and branch in this repo.

**Authorship.** The work is authored by the repo owner; Claude commits and is
credited as co-author. Set the author explicitly, since the harness's own git
identity is Claude:

```sh
GIT_COMMITTER_NAME="Claude" GIT_COMMITTER_EMAIL="noreply@anthropic.com" \
git commit --author="Adrian Tame <31286933+AdrianTJ@users.noreply.github.com>" -m "..."
```

Use the GitHub noreply address, matching the existing history, so a personal
email never lands in a public repo. End the message with the co-author trailer:

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

**Branch names.** Conventional prefixes — `feat/`, `bug/`, `chore/`, `docs/` —
followed by a short kebab-case description. Never put an agent's name in a
branch name, and never leave a generated suffix on one. Some harnesses default
to branch names like `claude/<topic>-<hash>`; rename before pushing.

```
feat/multi-harness-repo-structure     good
chore/rotate-herdr-sounds             good
claude/multi-harness-structure-ehxq   wrong: agent name, generated suffix
```

**Verify before pushing:**

```sh
git log --format='%h  A:%an  |  C:%cn' main..HEAD   # author you, committer Claude
git branch --show-current                           # feat/, bug/, chore/, docs/
```

## Rules

- **Never commit credentials.** `auth.json`, `models.json`, `.credentials.json`,
  `settings.local.json`, and session files are gitignored and unlinked by design.
  If a harness writes a secret into a tracked file, fix the manifest — don't
  loosen the gitignore.
- **Never link a whole config root.** `~/.claude` and `~/.pi/agent` hold
  credentials and session state alongside config. The manifest links individual
  files and directory entries for this reason.
- **`links.conf` is the only place symlinks are declared.** Adding a config file
  means adding a manifest line, not writing a symlink by hand.
- **Undo is available.** `./install.sh --unlink` removes only symlinks pointing
  into this repo and leaves everything else alone.

## Adding a config

1. Put the file in the harness folder — or `shared/` if a second harness reads
   the identical format.
2. Add a line to `links.conf` (`link` for one path, `merge` to link a
   directory's contents into a shared target).
3. `./install.sh --dry-run`, check the target path, then `./install.sh`.

**Skills that come from upstream get a `SOURCES.md` entry too.** If the file is
vendored from another repo or package, record its upstream, pinned revision,
and refresh procedure in `SOURCES.md` and put a short attribution footer in
the file itself. A skill without a source entry is a config change made
without its manifest line.

Each harness folder has its own README with that harness's exact path mapping
and gotchas. Read the relevant one before changing its config.
