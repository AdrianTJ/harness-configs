#!/usr/bin/env bash
#
# Structural checks for links.conf: four fields per line, known modes, and no
# duplicate `link` targets (`merge` targets repeat by design -- several
# sources feed one directory). Missing sources are reported, not errors:
# the manifest deliberately describes entries that aren't populated yet.
#
#   ./scripts/check-manifest.sh [path/to/links.conf]
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${1:-"$REPO_DIR/links.conf"}"

[[ -f "$MANIFEST" ]] || { echo "manifest not found: $MANIFEST" >&2; exit 1; }

fail=0
lineno=0
seen="$(mktemp)"; trap 'rm -f "$seen"' EXIT

while IFS= read -r line || [[ -n "$line" ]]; do
  lineno=$(( lineno + 1 ))
  case "$line" in ''|\#*) continue ;; esac
  set -f; set -- $line; set +f
  if [[ $# -ne 4 ]]; then
    echo "links.conf:$lineno: want 4 fields, got $#: $line" >&2
    fail=1; continue
  fi
  if [[ "$2" != link && "$2" != merge ]]; then
    echo "links.conf:$lineno: unknown mode '$2' (want link|merge)" >&2
    fail=1; continue
  fi
  if [[ "$2" == link ]]; then
    # Normalize ~-prefixed targets so `~/.x` and `$HOME/.x` compare equal.
    tgt="$4"; tgt="${tgt/#\~/\$HOME}"
    printf '%s\n' "$tgt" >> "$seen"
  fi
  if [[ ! -e "$REPO_DIR/$3" ]]; then
    echo "links.conf:$lineno: info: source not populated yet: $3"
  fi
done < "$MANIFEST"

dupes="$(sort "$seen" | uniq -d)"
if [[ -n "$dupes" ]]; then
  echo "duplicate link targets in links.conf:" >&2
  printf '%s\n' "$dupes" >&2
  fail=1
fi

exit "$fail"
