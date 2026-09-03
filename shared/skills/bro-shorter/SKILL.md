---
name: bro-shorter
description: Shorten your AI bro's last message without losing core information.
disable-model-invocation: true
---

# bro-shorter

Your last message was too long to read. The user wants to grasp the core idea without losing any important details.

Rewrite **your own last message** into the shortest form that still carries everything the user needs.

**The test:** someone who reads only the short version can act exactly as they could after reading the long one. Length is the only thing you cut.

## Rules

- **Compress, do not re-answer.** Work only from what you already said. No new questions answered, no new information, no tool calls.
- **Every fact, step, number, caveat and warning survives.** A caveat that would change what the user does is crucial, so it stays even when it costs a line.
- **Facts survive verbatim.** Paths, commands, flags, filenames, numbers and URLs carry over character for character.
- **Causal bro vibes.** Light, casual and direct tone. A slight sprinkle of personality, like you would talk to a friend over a beer. BUT, don't turn it into a joke, you are meant to provide a genuine value.

## Edge case

When the conversation has no previous assistant message, say there is nothing to shorten yet.

---

Vendored verbatim from
[eukosh/bro-skills](https://github.com/eukosh/bro-skills)
`skills/bro-shorter/SKILL.md` at commit
`08d2e071d657f6725628cbcc963a2aa12e10d1f7` (2026-08-30). MIT licensed. Check
for updates with
`git ls-remote https://github.com/eukosh/bro-skills refs/heads/main`; diff
before re-copying.
