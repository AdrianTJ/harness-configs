#!/bin/bash

INPUT=$(cat)
# Fail closed: if the command cannot be inspected, block rather than allow.
command -v jq >/dev/null 2>&1 || { echo "BLOCKED: jq unavailable, cannot inspect command." >&2; exit 2; }
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if [ -z "$COMMAND" ]; then
  echo "BLOCKED: could not parse tool command for safety inspection." >&2
  exit 2
fi

# Collapse runs of whitespace (tabs, double spaces) so spacing cannot dodge a match.
COMMAND_NORM=$(printf '%s' "$COMMAND" | tr -s '[:space:]' ' ')

# git global options may sit between "git" and the subcommand, e.g.
# `git -C dir push` or `git -c k=v push`.
G='git( +(-[cC] +[^ ]+|--?[A-Za-z][A-Za-z-]*(=[^ ]+)?))* +'

DANGEROUS_PATTERNS=(
  "${G}push"
  "${G}reset( +[^ ]+)* +--hard"
  "${G}clean( +[^ ]+)* +-[A-Za-z]*f"
  "${G}branch( +[^ ]+)* +-D"
  "${G}checkout +\\."
  "${G}restore +\\."
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if printf '%s' "$COMMAND_NORM" | grep -qE "$pattern"; then
    echo "BLOCKED: '$COMMAND' matches dangerous pattern '$pattern'. The user has prevented you from doing this." >&2
    exit 2
  fi
done

exit 0
