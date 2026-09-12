#!/usr/bin/env bash
# check-skill-refs.sh — official agentskills.io conformance via skills-ref.
# Complements validate-skills.py, which additionally checks this repo's
# evals layout (evals/evals.json per skill) that skills-ref doesn't know.
# Pinned to the skills-ref version tested locally; bump deliberately.
set -u
REF="skills-ref@0.1.5"
fail=0
for d in shared/skills/*/; do
  if out="$(npx -y "$REF" validate "$d" 2>&1)"; then
    echo "OK   $d (skills-ref)"
  elif grep -q 'Unexpected fields in frontmatter: disable-model-invocation' <<<"$out" \
    && [[ "$(grep -c '^  - ' <<<"$out")" == 1 ]]; then
    # Allowed deviation: the user-invoked-only flag is load-bearing host
    # convention (see bro-what/bro-shorter, vendored verbatim). Any skill may
    # carry exactly this one extra field; anything else still fails.
    echo "OK   $d (skills-ref, user-invoked-only flag)"
  else
    fail=1; echo "FAIL $d (skills-ref)"; echo "$out" | sed 's/^/     /'
  fi
done
exit "$fail"
