@~/.claude/AGENTS.md

# Claude Code

The import above is the harness-neutral half, shared with pi, codex, and
opencode. Everything below is Claude-specific and applies only here.

## Git

I author; you commit and take co-author credit. The author line is in the shared
instructions above — set the committer explicitly, since the harness's own git
identity is already Claude:

```sh
GIT_COMMITTER_NAME="Claude" GIT_COMMITTER_EMAIL="noreply@anthropic.com" \
git commit --author="Adrian Tame <31286933+AdrianTJ@users.noreply.github.com>" -m "..."
```

End every commit message with:

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

Check before pushing — author me, committer you:

```sh
git log --format='%h  A:%an  |  C:%cn' main..HEAD
```
