# pi-profiles: what was kept when it retired

[AdrianTJ/pi-profiles](https://github.com/AdrianTJ/pi-profiles) was a wrapper that gave pi per-profile config directories with a shared package pool. It was retired in November 2026: day-to-day work runs on plain pi (`pi/settings.json` here) with subagents and web search, and the profiles had become duplicates, empty shells, or finished trials. The repo is archived; its last state is tagged `v-final`.

This note keeps the lessons worth carrying forward.

## Unattended campaigns (the `marathon` profile)

Stack: `/goal` for intent, the Ralph loop (`@lnilluv/pi-ralph-loop`) for execution across fresh child sessions, `pi-tasks` for durable plans, `pi-nolo` for approval gating, `@plicara/pi-audit-loop` as a review gate.

Doctrine for long unattended runs:

- Verify against artifacts, never memory: tests, command output, files on disk, PR state. Plans and prior conversation are context, not proof.
- One task and one commit per iteration; progress goes in `RALPH_PROGRESS.md` every turn.
- Never emit the completion promise without running the acceptance commands fresh first.
- Blocked, budget-hit, or no progress: report and stop. Do not grind.
- Run in a git worktree, never the main checkout. Block `git push` and `npm publish`; protect secrets (`.env*`).
- Put a token budget on goals and `max_iterations` on loops.

Task dir anatomy: `RALPH.md` (YAML frontmatter with `max_iterations`, `timeout`, `completion_promise`, `required_outputs`, `guardrails.block_commands`, `guardrails.protected_files`, then the prompt as the body) plus `OPEN_QUESTIONS.md`, which must exist with no P0/P1 items or the completion gate blocks forever.

Morning routine: run the suite yourself, read `RALPH_PROGRESS.md` and `BUGS_FOUND.md` first, review commit by commit, revert ruthlessly, squash-merge survivors.

Best recorded run: 12 to 26 tests and 87% to 100% coverage in about 15 minutes, with no interventions.

## SoL-Pi trial

NVIDIA's [SoL-Pi](https://github.com/NVlabs/SoL-Pi) 0.1.0, Action Fusion and ObservationPack on. Measured 2026-09-12 against stock pi 0.85.1: with a natural prompt the model never opted into `then_run` (0 of 6 runs), so the extension was ObservationPack plus about 14% extra prompt overhead on small tasks. When the prompt asked for fusion it fired every time and saved a turn (4 to 3 turns, 12.7% to 21.6% fewer tokens). Not worth running by default.

## Extension collisions

`pi-nolo` re-registers the builtin `edit` and `bash` tools from pi's own definitions, and the first extension to register a tool keeps the slot. That silently strips parameters other extensions add (it disabled SoL-Pi's `then_run` for an entire trial). Never load two extensions that both re-register `edit`, `write`, or `bash`.
