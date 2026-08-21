# Global instructions

Applies everywhere, in every repo. Project-level `AGENTS.md` files layer on top
of this and win where they conflict.

Keep this file harness-neutral and short. Anything true of only one harness goes
in that harness's own folder — see `claude-code/CLAUDE.md` for the pattern.

## Git

Author every commit to me:

```
Adrian Tame <31286933+AdrianTJ@users.noreply.github.com>
```

Use that GitHub noreply address, never a personal email — it must not land in a
public repo.

Branch names take a conventional prefix (`feat/`, `bug/`, `chore/`, `docs/`)
followed by a short kebab-case description. **No model or vendor name in a
branch name, and no generated suffix.** Some harnesses default to names like
`claude/<topic>-<hash>`; rename before pushing.

```
feat/multi-harness-repo-structure     good
chore/prune-pi-extensions             good
claude/multi-harness-structure-ehxq   wrong: vendor name, generated suffix
```
