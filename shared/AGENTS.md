## Git
Author every commit to me: Adrian Tame <31286933+AdrianTJ@users.noreply.github.com>. Use that GitHub noreply address, never a personal email, it must not land in a repo. Never add a `Co-Authored-By` trailer, and never set an alternate committer identity.

Branch names take a conventional prefix (`feat/`, `bug/`, `chore/`, `docs/`) followed by a short kebab-case description. **No model or vendor name in a branch name, and no generated suffix.** Some harnesses default to names like `claude/<topic>-<hash>`; rename before pushing. For example: 
```
feat/multi-harness-repo-structure     good
chore/prune-pi-extensions             good
claude/multi-harness-structure-ehxq   wrong: vendor name, generated suffix
```

## Safety
Never commit secrets, tokens, or credential files (`.env`, `*.pem`, `credentials.json`). Verify with `git diff --cached` before committing.

## Approvals
Ask before destructive operations (`reset --hard`, `push --force`, `clean -fd`, publishing, deploys): state the command, wait for confirmation. Reads, edits, and test runs proceed without asking. Destructive git patterns are additionally enforced by hook where configured.

## Markdown
Write Markdown soft-wrapped: one paragraph per line, one list item per line, a blank line between blocks. Never hard-wrap prose at a column.

A newline in Markdown source is not a newline on the page, so wrapping buys nothing, and it renders wrong wherever newlines are treated as breaks: GitHub issue and PR bodies, chat, several docs sites. Keep line breaks only where they carry meaning, which is code blocks and tables.

If a file is already hard-wrapped, join the paragraphs you touch back into single lines rather than adding more wrapped ones. Do not reflow a whole file just to unwrap it; that buries the real change.

Procedures live in skills, not here — consult them for task workflows.
Keep this file to rules true in every repo.

