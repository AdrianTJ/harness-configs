---
name: log-decision
description: >
  Append a structured entry to a project's decision log. Use whenever a non-trivial
  decision is made, reversed, or a notable struggle/insight comes out of a
  conversation — language choices, architecture calls, scope cuts, "we tried X and it
  failed" moments.
---

# Log a decision

Append an entry to the project's decision log (commonly `docs/decision-log.md`;
create it there if the project doesn't have one yet). Never rewrite or delete past
entries — the log is append-only history. If a decision is reversed, the old entry
keeps its text and gets `Status: superseded by DEC-NNN`; the reversal is a new entry.

## Entry format

```markdown
## DEC-NNN: <short title>
- **Date:** YYYY-MM-DD
- **Status:** open | decided | superseded by DEC-NNN
- **Context:** Why this came up. Include the flavor of the conversation —
  disagreements, constraints, what prompted it.
- **Options considered:** Bullet list with one-line trade-offs each. Omit if trivial.
- **Decision:** What was chosen and the deciding reason(s).
- **Consequences:** What this commits us to, what it rules out, what to revisit later.
```

## Rules

- IDs are sequential (DEC-001, DEC-002, …). Read the log first to find the next ID.
- `open` entries are allowed — log the question before the answer exists.
- Struggles count: if significant time was burned on something, log what was tried
  and why it failed, even if no "decision" resulted. Use the same format with
  **Decision** describing the outcome/learning.
- Keep entries honest and specific. "We chose X because the lead prefers it" is a
  valid, loggable reason.

## Output

The appended `DEC-NNN` entry (new ID, correctly formatted), plus a one-line
confirmation of what was logged.

---

Ported from `AdrianTJ/agentic_engineering` (`.ruler/skills/general/log-decision`,
as of `87cb891`) with evals. No harness-configs-specific adaptation needed.
