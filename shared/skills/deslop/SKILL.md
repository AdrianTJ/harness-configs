---
name: deslop
description: Remove AI-generated slop from recently changed code — unrequested extras, comments that restate the code, needless abstractions, defensive handling for impossible cases, verbose naming, and generation artifacts like emoji or conversational comments. Use when asked to deslop, unslop, clean AI code, or remove AI patterns, and before committing a branch an agent wrote. For general quality review that may also restructure code, use simplify instead; for correctness bugs use code-review.
---

# Deslop

Slop is code that works and reads wrong: written by a model, shaped by habit
rather than by the problem. This skill removes it by **deletion under a behavior
lock** — every pass only takes things away, and behavior is proven unchanged
after each one.

If you find yourself designing rather than deleting, you have left this skill.
Redesign is a separate task.

## Hard gates

No exceptions to these.

1. **Lock behavior first.** Run the existing tests and confirm they pass. If the
   changed code has no coverage, add a regression test before touching it. No
   lock, no cleanup.
2. **One pass at a time.** Never mix two categories in one edit. Complete a pass,
   verify, then start the next.
3. **Verify after every pass.** If verification fails, revert that pass and
   investigate. Do not continue.
4. **Preserve behavior exactly.** If a removal changes observable behavior — even
   for the better — revert it and raise it separately.
5. **Stay in the diff.** Only touch what the branch changed. Nearby code that
   looks sloppy is out of scope.

## Scope

Work from the diff, not the whole repo:

```sh
git fetch origin
git diff origin/HEAD...HEAD --stat     # or against the branch's actual base
git diff origin/HEAD...HEAD
```

Skip any pass with zero findings, but run the passes that apply in order.

## Passes

### 1. Unrequested work

The highest-value deletions, because they remove whole additions rather than
trimming them.

- Features, refactors, and "improvements" beyond what was asked for
- Docstrings, type annotations, or comments added to code the change didn't touch
- New config knobs, hooks, or extension points nothing uses
- Files that exist to describe the work rather than do it (`PLAN.md`,
  `SUMMARY.md`, `NOTES.md`) unless the project keeps those

### 2. Dead code

- Unused imports, variables, parameters
- Unreachable branches, commented-out blocks
- Backwards-compatibility scar tissue for code that never shipped: variables
  renamed to `_unused`, re-exports kept "just in case", `// removed X` markers
- Empty handlers that swallow errors

Trust the tooling here — linters and compiler warnings find these faster than
reading does. Confirm a symbol is genuinely unreferenced before deleting it.

### 3. Comments that restate the code

- `// increment the counter` above `counter++`
- Doc blocks that repeat the signature and add nothing
- Section dividers (`// --- Helpers ---`) and file headers restating the filename

**Keep** comments that explain *why*, record a non-obvious constraint, or link an
issue or spec. A comment that would take a reader ten minutes to rediscover is
not slop.

### 4. Unnecessary abstractions

- Helpers called exactly once — inline them
- Wrappers that delegate everything to one inner object
- Factories that always produce the same thing
- Config objects for what will never be configured
- Interfaces with a single implementation and no second one in sight

The test: if removing the indirection makes the code shorter *and* no harder to
read, it was never earning its place. Three similar lines beat a premature
abstraction.

### 5. Defensive paranoia

- Null checks on values the type system already guarantees
- `try`/`catch` around code that cannot throw
- Validation of internal callers — validate at boundaries, not between your own
  functions
- Fallback defaults for required fields, which convert a loud failure into a
  silent one
- `as any`, `# type: ignore`, and friends used to bypass a type rather than
  satisfy it, plus type assertions the compiler doesn't need

**Keep** every check at a real boundary: user input, network, filesystem,
deserialization, anything crossing a trust line.

### 6. Naming

A name should be as short as it can be while staying unambiguous *in its scope*.
Wider scope earns a longer name; a short-lived local does not.

- `getUserDataFromDatabase` → `getUser`
- `user.userAccountStatus` → `user.status`
- `responseDataObject` → `response`
- `tempValueForCalculation` → inline it

### 7. Generation artifacts

- Emoji in code, comments, or commit messages, unless the project uses them
- Conversational comments: "Let's…", "Now we need to…", "Great!"
- Debug `print` / `console.log` left behind
- Code bent into a uniform template instead of the shape of the problem

## Verify

Use whatever the project actually uses, in rough order of speed: type-check,
lint, the tests covering the changed files, then the full suite once at the end.
Read the repo's config or docs to find the commands — do not assume a toolchain.

State plainly if you could not verify a pass, and why.

## Report

- The patterns found, with file and line
- What was deleted, per pass
- What you deliberately kept, and why — this matters more than the deletions
- Confirmation that behavior is unchanged, and how you know

## Anti-patterns

| Impulse | Why it fails |
|---|---|
| Batch every pass into one commit | A broken test can't be traced to a cause |
| "This abstraction is wrong, let me redesign it" | That's a design task, not cleanup |
| "Tests passed earlier, close enough" | A later pass can interact with an earlier one |
| "This nearby file is sloppy too" | Scope creep; the diff is the boundary |
| "It's only comments, no need to run tests" | Doc comments can be load-bearing (doctests, codegen, annotations) |
| Deleting a check because nothing currently hits it | Boundaries exist for inputs you haven't seen |

## Prevention

Cleaning after the fact is the fallback. Slop is cheaper to prevent at write
time by asking for the smallest change that works, so if you are running this
skill on every branch, fix the instructions upstream instead.

---

Adapted from two prior skills: the pattern catalogue in
[rohitg00/pro-workflow](https://github.com/rohitg00/pro-workflow) `deslop`, and
the pass discipline and gates in
[tmdgusya/engineering-discipline](https://github.com/tmdgusya/engineering-discipline)
`clean-ai-slop`.
