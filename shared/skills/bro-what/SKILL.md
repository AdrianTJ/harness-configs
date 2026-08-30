---
name: bro-what
description: Re-explain your AI bro's last message in so that you can actually understand it.
disable-model-invocation: true
---

# bro-what

The user read your last message and went "bro, what?". It was too dense,too verbose, too confusing, too jargon-heavy, or too formal.

Re-explain **your own most recent message** the way you would explain it to a sharp friend over a lunch break.

## Rules

- **Re-explain, do not re-answer.** Work only from what you already said. Never answer a new question, no new information, no tool calls.
- **Simpler, not shorter.** Take whatever space is requried for clarity. The goal is to fix "impossible to misunderstand", not "fewer words".
- **Facts survive verbatim.** Every path, command, flag, filename, number, URL, name and decision carries over character for character. Simplify the explanation around the facts, never the facts themselves.
- **Trade each jargon term for what it actually does.** Keep the original term in parentheses when the user will run into it again elsewhere.
- **Causal bro flavor.** Light, casual and direct: e.g. "Ok so basically", "the point is", "here is the thing". A slight touch of personality, don't turn it into a joke.
- **Same language in, same language out.** A German answer gets re-explained in German, a English one in English.
- **Flatten the structure.** Headers, tables and nested bullets become plain sentences. Keep a list only when the actual sequence is involved or where the original had genuinely parallel parts.
- **Open with the explanation.** The first sentence is content, not a preamble about what you are about to do.

## Edge case

When the conversation has no previous assistant message, say there is nothing to simplify yet.

---

Vendored verbatim from
[eukosh/bro-skills](https://github.com/eukosh/bro-skills)
`skills/bro-what/SKILL.md` at commit `08d2e071d657f6725628cbcc963a2aa12e10d1f7`
(2026-08-30). MIT licensed. Check for updates with
`git ls-remote https://github.com/eukosh/bro-skills refs/heads/main`; diff
before re-copying.
