# Skill sources

Ledger of where every skill in this repo came from, so updates can be checked
when needed. The counterpart of `links.conf` (which declares where files are
*symlinked*) — this declares where vendored skills are *fetched from*.

Every skill here is one of three things:

| Status | Meaning | Update policy |
|---|---|---|
| `vendored` | Copied into this repo, adapted for pi/Claude Code | Check upstream for changes, re-port, commit |
| `adapted` | Rewritten port; behavior or dialect differs from upstream | Check upstream for changes, re-apply the port, commit |
| `reference` | Not vendored — declared elsewhere in this repo | Check the registry/feed, bump the declaration |

Check for updates with the commands under each entry. When updating, do the
fetch into a scratch dir and `diff` against the vendored copy before touching
anything, then follow the attribution footer in the skill to note the new
revision.

**Pin format.** The `resolved_commit` column mirrors the lock file that Sentry's
dotagents (`agents.lock`) and the Vercel skills CLI (`.skill-lock.json`) both
write: the exact upstream revision the content was taken from, machine-checkable
rather than remembered. For GitHub sources that is the full commit SHA
(`git ls-remote <url> <ref>` verifies it); for npm packages it is the version
(`npm view <name> version`). Anything newer than the pin means a refresh is due.

## Summary

| Skill | Status | Upstream | resolved_commit | Checked | License |
|---|---|---|---|---|---|
| `unslop` | reference | [MohamedAbdallah-14/unslop](https://github.com/MohamedAbdallah-14/unslop) `skills/unslop/SKILL.md` | grabbed on demand | — | MIT |
| `deslop` | adapted | [rohitg00/pro-workflow](https://github.com/rohitg00/pro-workflow) `deslop`; [tmdgusya/engineering-discipline](https://github.com/tmdgusya/engineering-discipline) `clean-ai-slop` | `7f7209d…`, `137dead…` | 2026-07-18, 2026-07-03 | none declared |
| `bro-what` | vendored | [eukosh/bro-skills](https://github.com/eukosh/bro-skills) `skills/bro-what/SKILL.md` | `08d2e07…` | 2026-08-30 | MIT |
| `bro-shorter` | vendored | [eukosh/bro-skills](https://github.com/eukosh/bro-skills) `skills/bro-shorter/SKILL.md` | `08d2e07…` | 2026-08-30 | MIT |
| `ponytail` | reference | npm [`@dietrichgebert/ponytail`](https://www.npmjs.com/package/@dietrichgebert/ponytail) (GitHub: [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)) | `4.9.0` | — | MIT |
| `brainstorming` | adapted | [obra/superpowers](https://github.com/obra/superpowers) `skills/brainstorming/SKILL.md` | `b36e0829…` | 2026-09-03 | MIT |
| `harness-configs` | local | none — authored for this repo | — | — | — |
| `researcher` | local | none — authored for this repo (`pi/agents/`, no upstream) | — | — | — |
| `profile-badge` | vendored | [AdrianTJ/pi-profiles](https://github.com/AdrianTJ/pi-profiles) `extensions/profile-badge.ts` | `df7dbc0…` | 2026-09-12 | Apache-2.0 |
| `write-skill` | local | originally agentic_engineering; canonical home here | — | 2026-09-08 | — |
| `skill-creator` | reference | [anthropics/skills](https://github.com/anthropics/skills) `skills/skill-creator/SKILL.md` | via `npx skills` | — | Apache-2.0 |
| `validate-results` | local | originally agentic_engineering; canonical home here | — | 2026-09-09 | — |
| `log-decision` | local | originally agentic_engineering; canonical home here | — | 2026-09-09 | — |
| `sync-docs` | local | originally agentic_engineering; canonical home here | — | 2026-09-09 | — |
| `profile-pipeline` | local | created during eval scoring; reviewed and adopted | — | 2026-09-10 | — |

`harness-configs`, `write-skill`, `validate-results`,
`log-decision`, `sync-docs`, and `profile-pipeline` are local — no upstream. Everything else should be
re-checked periodically, and always before a significant upgrade of pi or
Claude Code.

---

## unslop

Humanize-LLM-output skill. **Not vendored** — grabbed on demand from upstream,
which is a single file needing no adaptation:

```sh
# Claude Code (any machine, when wanted)
npx skills add MohamedAbdallah-14/unslop -g -a claude-code
# or manual: clone https://github.com/MohamedAbdallah-14/unslop and copy skills/unslop/
```

Decision: stays reference-only. Nothing in the manifest consumes it, so it
is installed on demand per machine, never vendored here.


## deslop

Code-slop removal skill. Adapted from two upstreams (see its footer):
the pattern catalogue in `rohitg00/pro-workflow` `deslop` and the pass
discipline in `tmdgusya/engineering-discipline` `clean-ai-slop`.
Neither upstream declares a license — the adaptation is original enough to
stand alone, but re-distribution of verbatim upstream text is unlicensed.

```sh
git ls-remote https://github.com/rohitg00/pro-workflow HEAD        # resolved_commit 7f7209d
git ls-remote https://github.com/tmdgusya/engineering-discipline HEAD  # resolved_commit 137dead
# New commits? Review the upstream diffs, re-apply anything worth keeping, commit.
```


## bro-what & bro-shorter

"Explain that again like a human" skills from [eukosh/bro-skills](https://github.com/eukosh/bro-skills):
`bro-what` re-explains the last message plainly, `bro-shorter` compresses it.
Both are user-invoked only (`disable-model-invocation: true`), re-say without
re-answering, and are vendored verbatim (MIT) into `shared/skills/` — one
`SKILL.md` each. Upstream also ships an `agents/openai.yaml` per skill for
Codex's dialect; not vendored, since no linked target here feeds Codex skills.

```sh
git ls-remote https://github.com/eukosh/bro-skills refs/heads/main   # resolved_commit 08d2e07
# New commits? Diff upstream SKILL.md against the vendored copy, re-copy, update pin + footer.
```

Decision: Codex stays without a skills target — no manifest entry feeds
Codex skills, so the `openai.yaml` dialect ships upstream stay unvendored.
Revisit if Codex CLI documents a skills directory worth linking.

Measured lift (Muse Spark, 5 reps, 2026-09-10, `eval-runs/baseline.json`):
`bro-what` +4, `bro-shorter` −1. bro-shorter shows no proven lift — kept
deliberately: user-invoked cosmetics answer to a different bar than agentic
skills (style compliance on demand, not autonomous lift), and the eval stays
as a guardrail.

## brainstorming

Superpowers' design-before-code discipline, ported as **user-invoked
commands, not a skill** — deliberate, per the no-bloat rule: one TDD
doctrine (mattpocock `tdd`, installed via CLI below) and no competing
auto-triggers. Lives in four wrappers with one shared adapted body:

- `claude-code/commands/brainstorming.md` (`description` + `argument-hint`, `$ARGUMENTS`)
- `pi/prompts/brainstorming.md` (`description` + `argument-hint`, invocation text)
- `opencode/command/brainstorming.md` (`description`, `$ARGUMENTS`)
- `codex/prompts/brainstorming.md` (frontmatter-free; codex prompt format unverified)

Adaptation vs upstream: visual-companion section cut (needs plugin
assets), writing-plans references replaced with the project's normal
planning workflow, spec path `docs/superpowers/specs/` → `docs/specs/`.
The sibling skills the source name-checks (`superpowers:test-driven-development`,
`superpowers:verification-before-completion`) are intentionally absent —
mattpocock `tdd` covers that ground.

```sh
git ls-remote https://github.com/obra/superpowers HEAD   # resolved_commit b36e0829
# New commits? Diff upstream skills/brainstorming/SKILL.md against a wrapper, re-apply the adaptation to all four, update pin + footers.
```

## pi package skills

Sweep of every package declared in `pi/settings.json` `packages[]` (latest
2026-09-09), and what it ships. Skills reach pi from exactly one of them
(ponytail); the rest are extensions only. All are `reference` — the
declaration is tracked in `pi/settings.json`, the bytes are re-fetched per
machine.

| Package | Version | Ships | Source |
|---|---|---|---|
| `npm:@dietrichgebert/ponytail` | 4.9.0 | 6 skills (`ponytail`, `-audit`, `-debt`, `-gain`, `-help`, `-review`), pi extension, opencode plugin | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) |
| `npm:pi-subagents-lite` | 1.13.1 | extension | [AlexParamonov/pi-subagents-lite](https://github.com/AlexParamonov/pi-subagents-lite) |
| `npm:@bacnh85/pi-fff` | 0.8.0 | extension | [bacnh85/pi-extensions](https://github.com/bacnh85/pi-extensions) |
| `npm:@jqwn/pi-ask-user-question` | 0.2.0 | extension | [jqwn/pi-ask-user-question](https://github.com/jqwn/pi-ask-user-question) |
| `npm:@narumitw/pi-btw` | 0.58.1 | extension | [narumiruna/pi-extensions](https://github.com/narumiruna/pi-extensions) |
| `npm:pi-tasks` | 0.2.7 | extension | [nczz/pi-tasks](https://github.com/nczz/pi-tasks) |
| `npm:pi-web-lite` | 0.1.6 | extension | [smithyyang/pi-web-lite](https://github.com/smithyyang/pi-web-lite) |

Check per package: `npm view <name> version`. Bump by editing `pi/settings.json`;
pi installs the new version on startup.

The other skills pi sees — `deslop` and `harness-configs` — are linked from
`shared/skills/` (entries above). `pi/skills/` (local,
currently empty) is for pi-only skills authored here.

## ponytail

"Lazy senior dev" mode. **Not vendored** — it ships as an npm package that
carries a pi extension + skills and an opencode plugin, and it is declared in
two places here:

- `pi/settings.json` → `packages[]` (`npm:@dietrichgebert/ponytail`, deliberately
  unpinned — see `pi/README.md`)
- `opencode/opencode.json` → `plugin[]` (`@dietrichgebert/ponytail`, the exact
  form from the package README's OpenCode section)

```sh
npm view @dietrichgebert/ponytail version   # current upstream, compare against 4.9.0
# Bump by editing pi/settings.json (and opencode/opencode.json when present);
# pi installs the new version on startup. No files are copied into this repo.
```

The unpacked package also carries a `SKILL.md` for pi. If you want it visible
to Claude Code too, either vendor it here or accept pi-only.

## pi-subagents-lite

Delegation for pi — subagents, foreground or background, with steering,
continuation, worktrees, and an `/agents` management menu. Swapped in for
`pi-subagents` (2026-09-03): schema-first with three tools and no tool
descriptions, against a measured extension layer of ~16.7k of pi's ~22.5k
resident tokens. What the swap gives up: council-mode, saved workflows,
missions, and the two skills + five prompts the old package shipped (its
`council-mode` skill was the one that looked orphaned in pi's startup skill
list). Custom agents are plain `.md` files in `~/.pi/agent/agents/`.

```sh
npm view pi-subagents-lite version   # current upstream, compare against 1.13.1
# Bump by editing pi/settings.json; pi installs the new version on startup.
```

## harness-configs

Local skill for operating this repo (install/sync/repair runbook). No upstream;
edit in place. Do not check for updates — it *is* the source.

## sol-pi (profile package, not base)

[NVIDIA Labs SoL-Pi](https://github.com/NVlabs/SoL-Pi) — efficiency extension
for pi (Action Fusion, ObservationPack, reducer, context compact). **Not
vendored, not a base package** — declared in the `sol-trial` profile
(`git:github.com/NVlabs/SoL-Pi`, `0.1.0`, MIT).

The 2026-09-11 trial ran in a profile that had been cloned from `marathon`, so it
carried marathon's ten packages on top of SoL-Pi. One of them, `pi-nolo`,
re-registers the builtin `edit` tool and holds the `edit` slot ahead of SoL-Pi,
which removes Action Fusion's `then_run` parameter from the schema the model
receives. Action Fusion was therefore inert for `edit` calls for the entire trial
(`write` still fused), so the original "no measurable effect" verdict measured
ObservationPack plus a disabled fusion, not SoL-Pi. That profile is preserved as
`sol-marathon`; `sol-trial` is SoL-Pi only now. Do not load `pi-nolo` alongside
SoL-Pi: both register `edit` and the first one loaded takes the slot.

Also seen in that trial, not re-verified since: the extension does not load in
Ralph child sessions.

```sh
# No npm version to check; compare installed git rev against upstream HEAD
git ls-remote https://github.com/NVlabs/SoL-Pi HEAD
```

## profile-badge

Footer extension showing the active pi-profile name. Vendored verbatim from
[AdrianTJ/pi-profiles](https://github.com/AdrianTJ/pi-profiles)
`extensions/profile-badge.ts` into `pi/extensions/` (linked to
`~/.pi/agent/extensions/`), so the base config shows `[name]` when launched
via the wrapper and stays quiet otherwise.

```sh
git ls-remote https://github.com/AdrianTJ/pi-profiles HEAD   # resolved_commit df7dbc0
# New commits? Diff upstream extensions/profile-badge.ts against pi/extensions/profile-badge.ts, re-copy, update pin + footer.
```

## write-skill

House-style skill for authoring skills. Originally from agentic_engineering;
canonical home is this repo — edit in place, no upstream refresh. Evals in
`evals/evals.json`, with one assertion covering the `SOURCES.md` ledger step
this repo requires.

## skill-creator

Anthropic's skill-authoring skill (interview → draft → benchmark). **Not
vendored** — installed per machine from upstream, which needs no adaptation:

```sh
npx skills add anthropics/skills --skill skill-creator -g -a pi -a claude-code -a opencode
```

Decision: stays reference-only, like `unslop`. `write-skill` defers to it for
the drafting process; this entry records where it comes from.

Deliberately uninstalled from this machine 2026-09-11 (daily curation).
Reinstall with the command above; `write-skill` degrades gracefully without it.

## validate-results, log-decision, sync-docs

General-purpose working skills — trace every figure to its source, append-only
decision log, docs-vs-code audit. Originally from agentic_engineering;
canonical home is this repo — edit in place, no upstream refresh.

## profile-pipeline

Pipeline-bottleneck skill (time, bisect by prefix, fix by class, re-measure).
Created by a write-skill eval run that escaped its sandbox; quarantined,
reviewed (commands verified by hand), scored at +7 over 5 reps, then adopted.
No upstream; edit in place.

---

## Rules

- **Never vendor a skill without a source entry.** Adding `shared/skills/*`
  without a row in the summary table is the same mistake as a symlink without
  a `links.conf` line.
- **Pin what you fetch.** Record the exact commit (or version) and date you
  took, in this file *and* in the skill's footer — the `resolved_commit`
  convention, checkable with `git ls-remote` / `npm view`.
- **Record license state.** Skills with no declared license (`deslop`'s
  upstreams) are usable but not redistributable verbatim — say so.
- **Refresh in place.** Diff before copying, re-apply the adaptation, update
  the pin, commit. Never copy over the vendored copy unread.