# shared/

Config that more than one harness consumes in the same format. If something
needs translating per harness, it does not belong here.

| Path | Consumed by | Notes |
|---|---|---|
| `AGENTS.md` | pi, codex, opencode (as `AGENTS.md`); Claude Code (as `CLAUDE.md`) | One file, five links. |
| `skills/` | pi (`~/.pi/agent/skills`), Claude Code (`~/.claude/skills`), the store (`~/.agents/skills`) | The Agent Skills standard, so a `SKILL.md` directory drops into each unchanged. The store is read natively by opencode, Gemini CLI, Cursor and Codex. |
| `prompts/` | pi (`~/.pi/agent/prompts`), codex (`~/.codex/prompts`) | Both expand markdown files as `/name`. |

## Skills

One directory per skill, each containing `SKILL.md` with YAML frontmatter:

```
shared/skills/my-skill/
├── SKILL.md          # frontmatter: name, description
├── reference.md      # optional supporting files
└── scripts/
```

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
