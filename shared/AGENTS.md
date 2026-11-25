## Git
Branch names take a conventional prefix (`feat/`, `bug/`, `chore/`, `docs/`) followed by a short kebab-case description, with no model or vendor name and no generated suffix. Rename before pushing.

## Safety
Never commit secrets, tokens, or credential files (`.env`, `*.pem`, `credentials.json`); check `git diff --cached` before committing.

Ask before destructive operations (`reset --hard`, `push --force`, `clean -fd`, publishing, deploys): state the command and wait for confirmation. Reads, edits, and test runs go ahead without asking.

## Markdown
Soft-wrap: one paragraph or list item per line, a blank line between blocks, never hard-wrapped prose. Join wrapped paragraphs you touch; don't reflow whole files.

## Skills
Procedures live in skills. Load `sync-docs` when asked to update, sync, or refresh docs.
