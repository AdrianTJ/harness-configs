---
name: sync-docs
description: >
  Audit and refresh a project's documentation so it matches the current code and
  recent conversations. Use after a meaningful chunk of work, before ending a work
  session, or whenever docs feel stale.
---

# Sync docs

Bring the project's docs back in line with reality. Docs are the durable record of a
project's intent and decisions; code changes fast and docs don't follow on their own,
so drift is the default outcome unless something actively corrects it.

## Procedure

1. **Locate the docs.** Find wherever the project keeps its documentation. Check, in
   order: a top-level `docs/` directory; failing that, root-level files like
   `README.md` and `AGENTS.md`/`CLAUDE.md` (many projects have no dedicated docs
   directory at all — the root-level files *are* the docs). Skim each doc, then read
   the current code it's supposed to describe (structure, entry points, module
   responsibilities).
2. **Diff docs against reality.** For each doc, note what is stale, missing, or wrong:
   - An architecture/design doc — does it describe the code as it exists now? Are
     components, data flow, and boundaries accurate? Are "planned vs. built" sections
     labeled correctly?
   - A decision log, if the project keeps one — are there decisions made in recent
     work/conversation that were never logged? Log them via the `log-decision` skill
     (append-only — never edit past entries here).
   - Any other doc — same treatment.
3. **Fix.** Update the docs. Prefer correcting and pruning over appending; stale text
   is worse than no text. A decision log is the one exception (append-only).
4. **Report.** Tell the user what changed in each doc and anything you found that
   needs their input (e.g., an undocumented decision you couldn't reconstruct).

## Rules

- No filler. If a section would just restate the code without adding understanding,
  cut it.
- Docs describe intent and rationale, not just structure — "what and why", the code
  already shows "how".
- If code and docs conflict and you can't tell which is right, flag it to the user
  instead of guessing.

## Output

A per-doc summary of what changed (or "no change needed"), plus any conflicts or
undocumented decisions flagged for the user.

---

Ported from `AdrianTJ/agentic_engineering` (`.ruler/skills/general/sync-docs`,
as of `87cb891`) with evals. No harness-configs-specific adaptation needed.
