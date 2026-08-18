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
| `research-paper-writing` | adapted port | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) `skills/research/research-paper-writing/` | `5598215…` (v1.1.0) | 2026-08-08 | MIT |
| `deslop` | adapted | [rohitg00/pro-workflow](https://github.com/rohitg00/pro-workflow) `deslop`; [tmdgusya/engineering-discipline](https://github.com/tmdgusya/engineering-discipline) `clean-ai-slop` | `7f7209d…`, `137dead…` | 2026-07-18, 2026-07-03 | none declared |
| `ponytail` | reference | npm [`@dietrichgebert/ponytail`](https://www.npmjs.com/package/@dietrichgebert/ponytail) (GitHub: [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)) | `4.9.0` | — | MIT |
| `pi-subagents` | reference | npm [`pi-subagents`](https://www.npmjs.com/package/pi-subagents) (GitHub: [nicobailon/pi-subagents](https://github.com/nicobailon/pi-subagents)) | `0.51.0` | — | MIT |
| `harness-configs` | local | none — authored for this repo | — | — | — |

`harness-configs` is the only skill with no upstream. Everything else should be
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

## research-paper-writing

Full ML-paper pipeline (experiment design → submission) with LaTeX templates.
Ported into `shared/skills/research-paper-writing/` with the Hermes tool
dialect translated to harness-neutral equivalents (see its footer and
`references/sources.md` for the upstream history).

```sh
# Check for updates
curl -s "https://api.github.com/repos/NousResearch/hermes-agent/commits?path=skills/research/research-paper-writing/SKILL.md&per_page=1" \
  | python3 -c "import json,sys; c=json.load(sys.stdin)[0]; print(c['sha'], c['commit']['committer']['date'])"
# Compare against resolved_commit 5598215. New commit? Then:

# Refresh
git clone --depth 1 https://github.com/NousResearch/hermes-agent /tmp/hermes-agent
diff -r /tmp/hermes-agent/skills/research/research-paper-writing shared/skills/research-paper-writing
# re-apply the port (frontmatter, Agent Collaboration Patterns section, reference trims),
# update the resolved_commit in the footer, commit
```

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

## pi package skills

Sweep of every package declared in `pi/settings.json` `packages[]` (2026-08-18),
and what it ships. Skills reach pi from exactly two of them; the rest are
extensions only. All are `reference` — the declaration is tracked in
`pi/settings.json`, the bytes are re-fetched per machine.

| Package | Version | Ships | Source |
|---|---|---|---|
| `npm:@dietrichgebert/ponytail` | 4.9.0 | 6 skills (`ponytail`, `-audit`, `-debt`, `-gain`, `-help`, `-review`), pi extension, opencode plugin | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) |
| `npm:pi-subagents` | 0.51.0 | 1 skill (`pi-subagents`), 5 prompts | [nicobailon/pi-subagents](https://github.com/nicobailon/pi-subagents) |
| `npm:@bacnh85/pi-fff` | 0.7.9 | extension | [bacnh85/pi-extensions](https://github.com/bacnh85/pi-extensions) |
| `npm:@jqwn/pi-ask-user-question` | 0.2.0 | extension | [jqwn/pi-ask-user-question](https://github.com/jqwn/pi-ask-user-question) |
| `npm:@narumitw/pi-btw` | 0.54.1 | extension | [narumiruna/pi-extensions](https://github.com/narumiruna/pi-extensions) |
| `npm:pi-tasks` | 0.2.3 | extension | [nczz/pi-tasks](https://github.com/nczz/pi-tasks) |
| `npm:pi-web-access` | 0.24.0 | extension | [nicobailon/pi-web-access](https://github.com/nicobailon/pi-web-access) |

Check per package: `npm view <name> version`. Bump by editing `pi/settings.json`;
pi installs the new version on startup.

The other skills pi sees — `deslop`, `harness-configs`, `research-paper-writing`
— are linked from `shared/skills/` (entries above). `pi/skills/` (local,
currently empty) is for pi-only skills authored here.

## ponytail

"Lazy senior dev" mode. **Not vendored** — it ships as an npm package that
carries a pi extension + skills and an opencode plugin, and it is declared in
two places here:

- `pi/settings.json` → `packages[]` (`npm:@dietrichgebert/ponytail`, deliberately
  unpinned — see `pi/README.md`)
- `opencode/opencode.json` → plugin entry (once that file is populated)

```sh
npm view @dietrichgebert/ponytail version   # current upstream, compare against 4.9.0
# Bump by editing pi/settings.json (and opencode/opencode.json when present);
# pi installs the new version on startup. No files are copied into this repo.
```

The unpacked package also carries a `SKILL.md` for pi. If you want it visible
to Claude Code too, either vendor it here or accept pi-only.

## pi-subagents

Delegation for pi — subagents, foreground or background. Ships one skill
(`pi-subagents`) and five prompts, declared in `pi/settings.json` →
`packages[]`.

```sh
npm view pi-subagents version   # current upstream, compare against 0.51.0
# Bump by editing pi/settings.json; pi installs the new version on startup.
```

## harness-configs

Local skill for operating this repo (install/sync/repair runbook). No upstream;
edit in place. Do not check for updates — it *is* the source.

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