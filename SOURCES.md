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

## Summary

| Skill | Status | Upstream | Pinned | Checked | License |
|---|---|---|---|---|---|
| `unslop` | vendored (trimmed) | [MohamedAbdallah-14/unslop](https://github.com/MohamedAbdallah-14/unslop) `skills/unslop/SKILL.md` | `5af59d9` | 2026-05-05 | MIT |
| `research-paper-writing` | adapted port | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) `skills/research/research-paper-writing/` | `5598215` (v1.1.0) | 2026-08-08 | MIT |
| `deslop` | adapted | [rohitg00/pro-workflow](https://github.com/rohitg00/pro-workflow) `deslop`; [tmdgusya/engineering-discipline](https://github.com/tmdgusya/engineering-discipline) `clean-ai-slop` | `7f7209d`, `137dead` | 2026-07-18, 2026-07-03 | none declared |
| `ponytail` | reference | npm [`@dietrichgebert/ponytail`](https://www.npmjs.com/package/@dietrichgebert/ponytail) (GitHub: [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)) | `4.9.0` | — | MIT |
| `harness-configs` | local | none — authored for this repo | — | — | — |

`harness-configs` is the only skill with no upstream. Everything else should be
re-checked periodically, and always before a significant upgrade of pi or
Claude Code.

---

## unslop

Humanize-LLM-output skill. Vendored as
`shared/skills/unslop/SKILL.md` (single file, like `deslop`), with references
to the upstream project's own CLI and hooks trimmed.

```sh
# Check for updates
git ls-remote https://github.com/MohamedAbdallah-14/unslop HEAD
# Compare against pinned 5af59d9. New commit? Then:

# Refresh
curl -sL "https://raw.githubusercontent.com/MohamedAbdallah-14/unslop/<sha>/skills/unslop/SKILL.md" -o /tmp/unslop-new.md
diff shared/skills/unslop/SKILL.md /tmp/unslop-new.md
# re-apply the trims, update the pinned SHA in the footer, commit
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
# Compare against pinned 5598215. New commit? Then:

# Refresh
git clone --depth 1 https://github.com/NousResearch/hermes-agent /tmp/hermes-agent
diff -r /tmp/hermes-agent/skills/research/research-paper-writing shared/skills/research-paper-writing
# re-apply the port (frontmatter, Agent Collaboration Patterns section, reference trims),
# update the pinned SHA in the footer, commit
```

## deslop

Code-slop removal skill. Adapted from two upstreams (see its footer):
the pattern catalogue in `rohitg00/pro-workflow` `deslop` and the pass
discipline in `tmdgusya/engineering-discipline` `clean-ai-slop`.
Neither upstream declares a license — the adaptation is original enough to
stand alone, but re-distribution of verbatim upstream text is unlicensed.

```sh
git ls-remote https://github.com/rohitg00/pro-workflow HEAD        # pinned 7f7209d
git ls-remote https://github.com/tmdgusya/engineering-discipline HEAD  # pinned 137dead
# New commits? Review the upstream diffs, re-apply anything worth keeping, commit.
```

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

## harness-configs

Local skill for operating this repo (install/sync/repair runbook). No upstream;
edit in place. Do not check for updates — it *is* the source.

---

## Rules

- **Never vendor a skill without a source entry.** Adding `shared/skills/*`
  without a row in the summary table is the same mistake as a symlink without
  a `links.conf` line.
- **Pin what you fetch.** Record the exact commit (or version) and date you
  took, in this file *and* in the skill's footer.
- **Record license state.** Skills with no declared license (`deslop`'s
  upstreams) are usable but not redistributable verbatim — say so.
- **Refresh in place.** Diff before copying, re-apply the adaptation, update
  the pin, commit. Never copy over the vendored copy unread.