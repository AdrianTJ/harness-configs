# shared/

Config that more than one harness consumes in the same format. If something
needs translating per harness, it does not belong here.

| Path | Consumed by | Notes |
|---|---|---|
| `AGENTS.md` | pi, codex, opencode (as `AGENTS.md`); Claude Code (imported by `claude-code/CLAUDE.md`) | Harness-neutral only. Claude-specific rules live in `claude-code/CLAUDE.md`, which imports this file. |
| `skills/` | pi (`~/.pi/agent/skills`), Claude Code (`~/.claude/skills`), the store (`~/.agents/skills`) | The Agent Skills standard, so a `SKILL.md` directory drops into each unchanged. The store is read natively by opencode (verified here) and Gemini CLI (documented alias). |
| `prompts/` | pi (`~/.pi/agent/prompts`), codex (`~/.codex/prompts`) | Both expand markdown files as `/name`. |

## Skills

One directory per skill, each containing `SKILL.md` with YAML frontmatter:

```
shared/skills/my-skill/
├── SKILL.md          # frontmatter: name, description
├── reference.md      # optional supporting files
└── scripts/
```

A skill may also set `disable-model-invocation: true` to make it user-invoked
only — triggered by `/name`, never auto-selected by the model. Current set:
`bro-what`, `bro-shorter`, `deslop`, `write-skill`. The conformance check
(`scripts/check-skill-refs.sh`) allows exactly that one extra frontmatter field
as a deviation from the strict spec; any other unexpected field still fails.

## Skill evals

Each skill ships at least one case in `evals/evals.json`: a realistic request that never names the skill, an `expected_output` sketch, output-facing `assertions`, and optional `transcript_assertions` for evidence that can only be checked from the process. A case may run deterministic `setup` commands in both target arms and may use `{ "source", "dest" }` fixture entries when the workspace layout matters. `skill_name` matches the directory, IDs are unique, and fixtures live under `evals/files/`. `scripts/validate-skills.py` checks this structure in CI.

Assertions describe observable behavior rather than wording. They must be checkable against evidence the response earned: “previewed before linking” survives rewording, while “the reply contains `--dry-run`” does not. Where fabrication is possible, include an honesty assertion and make the requested behavior performable with a fixture.

Scored runs use Pi JSON event mode. Each target and control arm retains raw events, a compact transcript summary, observed model and usage, tool calls, files read or modified, commands, errors, and non-secret environment manifests. The primary result is binary task pass/fail; assertion scores remain diagnostic detail.

The judge must be pinned explicitly with `EVAL_JUDGE_PROVIDER` and `EVAL_JUDGE_MODEL`. Running the same provider/model as both target and judge stops the run unless `EVAL_ALLOW_SELF_JUDGE=1` is set for an explicitly exploratory experiment.

Every run records per-case fingerprints over the skill, that case and fixtures, runner code, target/judge configuration, timeout, repetitions, pi version, and effective non-secret profile runtime. `python3 scripts/eval-status.py <run-directory>` checks freshness without model calls; `--check` exits nonzero for stale or missing cases. Raw runs remain in gitignored `eval-runs/`; reviewed summaries belong in tracked `eval-baselines/`.

## Trigger probes

Scored evals force-load their skill, so they measure compliance, not routing. `trigger_probes` measure automatic selection using a realistic prompt that never names the skill. Set `expect_activation: false` for a relevant negative request; results then report false-positive activation instead of a miss rate. The linked arm receives a copied skill catalog; the isolated control omits only the target. Both retain JSON transcripts and environment manifests. Results report output-fingerprint activation, control contamination, and whether the transcript directly read the target `SKILL.md`. User-invoked `bro-what` and `bro-shorter` are exempt.

`install.sh` links each skill directory individually into every harness that
takes skills, so a harness-only skill can still live in `pi/skills/` or
`claude-code/skills/` without conflict.

Skills that come from outside this repo are vendored or referenced through the
ledger in [`SOURCES.md`](../SOURCES.md) at the repo root — every vendored
skill records its upstream, pinned revision, and refresh procedure there and in
its own attribution footer. Check it before adding or updating a skill.

## Prompts vs commands

Prompt templates are markdown that expands on `/name`. The bodies are portable;
the frontmatter is not — Claude Code's `commands/` supports keys (`allowed-tools`,
`argument-hint`) that pi and codex ignore or reject. Keep frontmatter-free
prompts here, and put anything that needs harness-specific frontmatter in that
harness's own `commands/` or `prompts/` directory.

opencode's `command/` is not linked from here for the same reason: it expects
its own frontmatter shape. Add wrappers under `opencode/command/` that point at
shared content if you want to reuse a body.
