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
    --dry-run)
      if [[ -e "$te" && ! -L "$te" ]]; then
        echo "backup+link $te (real file will be preserved)"
      else
        echo "would link $te"
      fi
      ;;
    --status) echo "needs-link $te";;
    *)
      mkdir -p "$(dirname "$te")"
      if [[ -e "$te" && ! -L "$te" ]]; then
        backup="${te}.bak-$(date +%Y%m%d%H%M%S)"
        mv "$te" "$backup"
        echo "backup    $te -> $backup"
      elif [[ -L "$te" ]]; then
        rm "$te"
      fi
      ln -s "$PWD/$src" "$te"
      echo "linked    $te"
      ;;
  esac
done < links.conf
echo "status: $n_ok already ok"
