---
name: write-skill
description: Write or revise an Agent Skill so it conforms to the Agent Skills spec and is actually reliable — description that triggers correctly, checkable steps, progressive disclosure. Use when adding a skill, or when reviewing an existing one for quality.
---

# Write skill

A skill exists to wrangle determinism out of a stochastic system: its virtue is
**predictability** — the agent taking the same *process* every run, not producing
the same output. Everything below serves that.

## Workflow

1. **Confirm it doesn't already exist.** Search the skills already available for
   something covering the job, and check whether Anthropic maintains one
   ([anthropics/skills](https://github.com/anthropics/skills) — `docx`, `pdf`,
   `pptx`, `xlsx`, `skill-creator` and more). Prefer referencing theirs over
   writing your own when the job is genuinely the same; compose, don't duplicate.
   This repo's policy: upstream skills that need no adaptation stay out of git
   and install via `npx skills add` (see `SOURCES.md`); only adapted or local
   skills get vendored here.
2. **Draft the content.** If `skill-creator` is available (it installs into
   `~/.agents/skills/` via `npx skills add anthropics/skills --skill
   skill-creator`), use its interview → draft → benchmark process — it is better
   at this than improvising, and it measures whether the skill actually changed
   behavior. Elsewhere, follow the rest of this workflow directly.
3. **Place it and name it.** One directory per skill, containing `SKILL.md`. The
   spec requires the frontmatter **`name` to match the directory name exactly**:
   1–64 characters, lowercase alphanumerics separated by single hyphens.
   In this repo: `shared/skills/<name>/` for anything two or more harnesses read
   verbatim, a harness folder (`pi/skills/`, `claude-code/skills/`) for
   harness-only skills. `merge` entries in `links.conf` pick up new directories
   automatically — verify with `./install.sh --dry-run`, then `./install.sh`.
4. **Write the description as the trigger.** It is the *only* thing an agent sees
   when deciding to load the skill, so it must say what the skill does AND when
   to use it. Front-load the leading verb ("Explore a dataset…"), cover the
   phrasings a user would actually say, one trigger per situation — no synonym
   padding. Cap 1024 characters.
5. **Write the body as checkable steps.** Numbered workflow where each step has a
   completion state a reader can verify; guardrails only for real failure modes;
   an Output section stating what the skill hands to whatever runs next. Name
   sibling skills it feeds or consumes.
6. **Disclose progressively.** The body holds the steps; anything consulted on
   demand goes to `references/` or `scripts/` beside the SKILL.md. Keep the body
   short enough to scan — under ~150 lines — with a short index pointing at the
   references.
7. **Verify anything you claim.** Run every command you document before shipping
   it. This is the step people skip and the one that catches real bugs.
   Writing a recipe and believing it is not the same as running it.
8. **Add evals.** At least one per skill, as `evals/evals.json` beside the
   `SKILL.md`: a realistic request written as a user would say it (without
   naming the skill, or the eval only proves the model can follow an instruction
   you already gave it), plus assertions describing what a good response does.
9. **Ledger it.** Every skill gets a row in `SOURCES.md` (upstream, pin,
   license) and, if vendored or adapted, a footer below noting the source.
   No ledger row, no merge — same rule as a symlink without a `links.conf` line.

## Prune

Delete any sentence that doesn't change what the agent would do — don't reword
it. One source of truth per fact: project-wide rules belong in the project's own
`AGENTS.md`, not copied into every skill.

## Output

A spec-conforming `SKILL.md` (plus any `references/`/`scripts/`), at least one
eval in `evals/evals.json`, and a `SOURCES.md` row — symlinked into place and
verified with `./install.sh --status`.

---

Ported from `AdrianTJ/agentic_engineering` (`.ruler/skills/general/write-skill`,
as of `71ae28e`) and adapted to this repo's layout: placement, ledger, and
`skill-creator`-via-ecosystem-store steps are harness-configs-specific. The
canonical home is now here.
