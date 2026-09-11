#!/bin/bash

INPUT=$(cat)
# Fail closed: if the command cannot be inspected, block rather than allow.
command -v jq >/dev/null 2>&1 || { echo "BLOCKED: jq unavailable, cannot inspect command." >&2; exit 2; }
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if [ -z "$COMMAND" ]; then
  echo "BLOCKED: could not parse tool command for safety inspection." >&2
  exit 2
fi

DANGEROUS_PATTERNS=(
  "git push"
  "git reset --hard"
  "git clean -fd"
  "git clean -f"
  "git branch -D"
  "git checkout \."
  "git restore \."
  "push --force"
  "reset --hard"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    echo "BLOCKED: '$COMMAND' matches dangerous pattern '$pattern'. The user has prevented you from doing this." >&2
    exit 2
  fi
done

exit 0
