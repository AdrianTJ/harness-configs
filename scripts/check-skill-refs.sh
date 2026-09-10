#!/usr/bin/env bash
# check-skill-refs.sh — official agentskills.io conformance via skills-ref.
# Complements validate-skills.py, which additionally checks this repo's
# evals layout (evals/evals.json per skill) that skills-ref doesn't know.
# Pinned to the skills-ref version tested locally; bump deliberately.
set -u
REF="skills-ref@0.1.5"
fail=0
for d in shared/skills/*/; do
  name="$(basename "$d")"
  if out="$(npx -y "$REF" validate "$d" 2>&1)"; then
    echo "OK   $d (skills-ref)"
  elif { [[ "$name" == "bro-what" ]] || [[ "$name" == "bro-shorter" ]]; } \
    && grep -q 'Unexpected fields in frontmatter: disable-model-invocation' <<<"$out" \
    && [[ "$(grep -c '^  - ' <<<"$out")" == 1 ]]; then
    # Known upstream deviation: user-invoked-only flag, load-bearing, and both
    # skills are vendored verbatim (see SOURCES.md) — must not "fix" by editing.
    echo "OK   $d (skills-ref, known upstream exception)"
  else
    fail=1; echo "FAIL $d (skills-ref)"; echo "$out" | sed 's/^/     /'
  fi
done
exit "$fail"
