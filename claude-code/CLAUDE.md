@~/.claude/AGENTS.md

# Claude Code

The import above is the harness-neutral half, shared with pi, omp, codex, and
opencode. Everything below is Claude-specific and applies only here.

## Git

I author every commit; you never attribute yourself — no `Co-Authored-By`
trailer, no alternate committer. Set the author explicitly, since the harness's
own git identity may differ:

```sh
git commit --author="Adrian Tame <31286933+AdrianTJ@users.noreply.github.com>" -m "..."
```

Check before pushing — author and committer both me:

```sh
git log --format='%h  A:%an  |  C:%cn' main..HEAD
```
