#!/usr/bin/env bash
# Fixture installer for the dry-run-before-link eval. Handles `link` lines:
#   <harness> link <src> <tgt>   (tgt may use $HOME, expanded at link time)
set -u
cd "$(dirname "$0")"
mode="${1:-install}"
expand() { eval printf '%s' "$1"; }
n_ok=0
while read -r _harness mode_word src tgt _rest; do
  [[ -z "${_harness:-}" || "$_harness" == \#* || "$mode_word" != link ]] && continue
  te="$(expand "$tgt")"
  if [[ -L "$te" && "$(readlink "$te")" == "$PWD/$src" ]]; then
    echo "ok        $te"; n_ok=$(( n_ok + 1 )); continue
  fi
  case "$mode" in
    --dry-run|--status) echo "would link $te";;
    *) mkdir -p "$(dirname "$te")"; ln -sf "$PWD/$src" "$te"; echo "linked    $te";;
  esac
done < links.conf
echo "status: $n_ok already ok"
