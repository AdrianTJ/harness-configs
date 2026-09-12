#!/usr/bin/env bash
# Everything the validate workflow runs, in one place so the same checks can run
# before a push instead of after. The workflow calls this file, and so does
# .githooks/pre-push, so CI and the local run cannot drift apart.
set -euo pipefail
cd "$(dirname "$0")/.."

SHELL_FILES=(install.sh scripts/check.sh scripts/check-manifest.sh scripts/check-skill-refs.sh scripts/check-upstream.sh)

command -v shellcheck >/dev/null 2>&1 || { echo "shellcheck is required: brew install shellcheck" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 1; }

echo "== shellcheck"
shellcheck -S warning "${SHELL_FILES[@]}"

echo "== syntax"
for f in "${SHELL_FILES[@]}"; do bash -n "$f"; done

echo "== manifest structure"
bash scripts/check-manifest.sh

echo "== skills and evals structure"
python3 scripts/validate-skills.py

echo "== spec conformance (skills-ref)"
bash scripts/check-skill-refs.sh

echo "== install smoke test"
./install.sh --dry-run
./install.sh --status

echo "== unknown harness rejected"
if ./install.sh --harness bogus --status; then
  echo "expected --harness bogus to fail" >&2
  exit 1
fi

echo "harness-configs: all checks passed"
