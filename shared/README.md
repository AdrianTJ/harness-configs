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

## Skill evals

Each skill ships at least one eval in `evals/evals.json` beside its `SKILL.md`:
a realistic request written as a user would say it (never naming the skill),
an `expected_output` sketch, and `assertions` a reviewer can check against a
response. Evals are behavioral checks, not tests — run them by eye when a
skill changes. See `write-skill/evals/evals.json` for the shape.

Assert behavior a reader could check, not phrasing — "dry-runs the fan-out
before executing" survives a rewording of the skill, "the reply contains
`--dry-run`" does not. Prefer stating the failure you're guarding against;
several assertions here came from bugs found by actually running the skills.
`skill_name` must match the skill's directory, `id` unique within the file.
Fixtures go in `evals/files/`, paths relative to the skill dir.
`scripts/validate-skills.py` checks every skill structurally (spec-conforming
frontmatter, well-formed evals) — run it before committing, CI runs it too.

## Trigger probes

Scored evals force-load their skill, so they measure compliance, not routing.
`trigger_probes` in `evals.json` measure whether the skill fires on its own: a
realistic prompt (never naming the skill), plus `fingerprints` — terms that
appear in this skill's `SKILL.md` and in no other skill. The driver links all
skills like a real install, runs the prompt under a clean-room HOME, and
compares against an unlinked control. bro-what/bro-shorter are user-invoked by
design and exempt. Machine-referential skills are out of scope: the
harness-configs probe was dropped because both arms confabulate repo
internals (install.sh invocations, link counts) without the skill, so no
fingerprint can distinguish activation from guessing.

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
