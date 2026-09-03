---
name: docs-freshness
description: Verify library, CLI, and API usage against current official docs before writing code that depends on them. Use when touching a fast-moving dependency, a version newer than training data, or any external API where being wrong is costly. Skip for this repo's own code, the standard library, and stable APIs already exercised by existing tests.
---

# Docs Freshness

Training data goes stale. Before writing code against an external API,
verify against today's docs, not memory.

## The reflex

1. **Spot the risk**: fast-moving ecosystems (agent tooling, web frameworks,
   cloud SDKs), a major version you can't date, or a flag/parameter you are
   quoting from memory.
2. **Pin the version**: check what is actually installed and what the project
   declares (`--version`, `npm view <pkg> version`, `cargo tree`, `pip show`,
   go.mod, ...) — installed version and latest docs may differ.
3. **Fetch the primary source**: official docs, changelog, or the source repo
   for the specific function or flag — not a blog post, not a tutorial.
4. **Trust the fetch over memory**: when docs contradict what you "know", the
   docs win. Say so explicitly: "docs as of <version/date> say X; my prior
   said Y."
5. **Cite what you checked**: when it matters (benchmarks, studies, released
   code), state the version the work targets.

## Escalation

- Docs unreachable or ambiguous → say so and mark the assumption in the code
  or output. Do not paper over it.
- Installed version differs from latest docs → target the installed version
  and flag the delta, or propose the upgrade as a separate decision.

Keep it proportional: a five-second version check for small things, a real
docs pass for anything load-bearing.
