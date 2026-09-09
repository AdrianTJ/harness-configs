---
name: validate-results
description: >
  Validate that every number, figure, and claim in a deliverable traces back to a real
  computed result before it ships. Use as the final step before delivering any deck,
  report, or summary containing numbers, or whenever asked to check that figures are
  right or where a number came from.
---

# Validate results

Every figure traces to a source, or it doesn't ship. This turns the guardrail "never
invent or round-trip numbers" into a checkable step instead of a hope.

## Workflow

1. **Enumerate the claims.** List every number, percentage, chart value, and
   directional claim ("grew", "fastest", "half of…") in the deliverable. Rounded and
   derived numbers count.
2. **Map each claim to its source.** For each, name the query, command, or file that
   produced it. A number whose source is "earlier in the conversation" is mapped to the
   actual command that computed it, not to memory of it.
3. **Re-verify the cheap ones.** Re-run inexpensive commands/queries and diff against
   the deliverable. For expensive ones, check the recorded output artifact instead.
4. **Check derived math and rounding.** Recompute percentages, deltas, and totals from
   their inputs; confirm chart visuals match the underlying values (axis truncation,
   mislabeled units).
5. **Flag, don't fudge.** Anything unreconciled is flagged explicitly in the
   deliverable or removed — never smoothed over. An honest "unverified" beats a
   confident wrong number.
6. **Append the trace table.** A short figure → source table (claim, value, producing
   command/query, verified yes/no) goes in the deliverable's appendix.

## Output

The validated deliverable plus its figure→source trace table, with any unverified
claims either removed or explicitly flagged.

---

Local skill; canonical home is this repo.
