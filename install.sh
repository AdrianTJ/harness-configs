#!/usr/bin/env bash
#
# Symlink harness configs from this repo into their real config directories.
# Driven entirely by links.conf -- nothing outside that manifest is touched.
#
#   ./install.sh                      link everything
#   ./install.sh --dry-run            show what would happen, change nothing
#   ./install.sh --harness pi         limit to one harness (repeatable)
#   ./install.sh --status             report current state, change nothing
#   ./install.sh --unlink             remove only the symlinks we created
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$REPO_DIR/links.conf"
: "${XDG_CONFIG_HOME:="$HOME/.config"}"

ACTION=install
DRY_RUN=0
FILTERS=()
STAMP="$(date +%Y%m%d%H%M%S)"

n_linked=0 n_ok=0 n_skipped=0 n_conflict=0 n_removed=0

if [[ -t 1 ]]; then
  C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_ERR=$'\033[31m'; C_DIM=$'\033[2m'; C_OFF=$'\033[0m'
else
  C_OK=""; C_WARN=""; C_ERR=""; C_DIM=""; C_OFF=""
fi

usage() { sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run|-n) DRY_RUN=1 ;;
    --status)     ACTION=status ;;
    --unlink)     ACTION=unlink ;;
    --harness)    [[ $# -ge 2 ]] || { echo "--harness needs a value" >&2; exit 2; }
                  FILTERS+=("$2"); shift ;;
    -h|--help)    usage; exit 0 ;;
    *)            echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

[[ -f "$MANIFEST" ]] || { echo "manifest not found: $MANIFEST" >&2; exit 1; }

# Expand only $HOME and $XDG_CONFIG_HOME -- no eval, so a stray backtick or
# $(...) in the manifest stays inert text.
expand() {
  local t="$1"
  t="${t/#\~/$HOME}"
  t="${t//\$XDG_CONFIG_HOME/$XDG_CONFIG_HOME}"
  t="${t//\$HOME/$HOME}"
  printf '%s' "$t"
}

wanted() {
  [[ ${#FILTERS[@]} -eq 0 ]] && return 0
  local f
  for f in "${FILTERS[@]}"; do [[ "$f" == "$1" ]] && return 0; done
  return 1
}

say() { # status colour, target, note
  local colour="$1" label="$2" target="$3" note="${4:-}"
  printf '  %s%-9s%s %s' "$colour" "$label" "$C_OFF" "${target/#$HOME/\~}"
  [[ -n "$note" ]] && printf ' %s(%s)%s' "$C_DIM" "$note" "$C_OFF"
  printf '\n'
}

run() { (( DRY_RUN )) && return 0; "$@"; }

# Is $1 a symlink pointing somewhere inside this repo?
ours() {
  [[ -L "$1" ]] || return 1
  local dest; dest="$(readlink "$1")"
  [[ "$dest" == "$REPO_DIR"/* ]]
}

unlink_one() { # absolute target
  local tgt="$1"
  if ours "$tgt"; then
    run rm -f "$tgt"; n_removed=$(( n_removed + 1 )); say "$C_OK" "removed" "$tgt"
  elif [[ -e "$tgt" || -L "$tgt" ]]; then
    n_skipped=$(( n_skipped + 1 )); say "$C_DIM" "skip" "$tgt" "not ours, left alone"
  fi
}

link_one() { # absolute source, absolute target
  local src="$1" tgt="$2"

  # Unlink is driven by the target, not the source: a link whose source was
  # since renamed or deleted still needs removing.
  if [[ "$ACTION" == unlink ]]; then unlink_one "$tgt"; return 0; fi

  if [[ ! -e "$src" ]]; then
    n_skipped=$(( n_skipped + 1 ))
    say "$C_DIM" "skip" "$tgt" "${src#"$REPO_DIR"/} not here yet"; return 0
  fi

  if [[ -L "$tgt" && "$(readlink "$tgt")" == "$src" ]]; then
    n_ok=$(( n_ok + 1 )); say "$C_OK" "ok" "$tgt"; return 0
  fi

  if [[ "$ACTION" == status ]]; then
    if [[ -L "$tgt" ]]; then
      if ours "$tgt"; then n_conflict=$(( n_conflict + 1 )); say "$C_WARN" "stale" "$tgt" "links elsewhere in repo"
      else n_conflict=$(( n_conflict + 1 )); say "$C_WARN" "foreign" "$tgt" "symlink not from this repo"; fi
    elif [[ -e "$tgt" ]]; then
      n_conflict=$(( n_conflict + 1 )); say "$C_WARN" "conflict" "$tgt" "real file in the way"
    else
      n_linked=$(( n_linked + 1 )); say "$C_DIM" "missing" "$tgt" "would link"
    fi
    return 0
  fi

  # install: back up anything real that is standing in the way
  if [[ -e "$tgt" || -L "$tgt" ]]; then
    if ours "$tgt"; then
      run rm -f "$tgt"
    else
      local backup="$tgt.bak-$STAMP"
      run mv "$tgt" "$backup"
      say "$C_WARN" "backup" "$tgt" "moved aside to $(basename "$backup")"
    fi
  fi

  run mkdir -p "$(dirname "$tgt")"
  run ln -s "$src" "$tgt"
  n_linked=$(( n_linked + 1 )); say "$C_OK" "linked" "$tgt"
}

process() { # harness, mode, source, target
  local mode="$2" src="$REPO_DIR/$3" tgt; tgt="$(expand "$4")"

  case "$mode" in
    link)
      link_one "$src" "$tgt" ;;
    merge)
      # Unlink sweeps the target directory instead of the source, so links whose
      # source has since been renamed or removed still get cleaned up.
      if [[ "$ACTION" == unlink ]]; then
        [[ -d "$tgt" ]] || return 0
        local existing
        for existing in "$tgt"/*; do
          [[ -L "$existing" ]] && unlink_one "$existing"
        done
        return 0
      fi

      if [[ ! -d "$src" ]]; then
        n_skipped=$(( n_skipped + 1 ))
        say "$C_DIM" "skip" "$tgt/" "$3 not here yet"; return 0
      fi
      local found=0 entry
      for entry in "$src"/*; do
        [[ -e "$entry" ]] || continue
        local base; base="$(basename "$entry")"
        # Skeleton markers and per-folder docs are not content to deploy.
        [[ "$base" == "README.md" || "$base" == ".gitkeep" ]] && continue
        found=1
        link_one "$entry" "$tgt/$base"
      done
      if (( ! found )); then
        n_skipped=$(( n_skipped + 1 ))
        say "$C_DIM" "skip" "$tgt/" "$3 is empty"
      fi ;;
    *)
      echo "unknown mode '$mode' in manifest" >&2; exit 1 ;;
  esac
}

case "$ACTION" in
  install) (( DRY_RUN )) && echo "Dry run -- nothing will be written." ;;
  status)  echo "Reporting current state only." ;;
  unlink)  echo "Removing symlinks that point into $REPO_DIR." ;;
esac

current=""
while read -r harness mode src tgt _rest; do
  [[ -z "${harness:-}" || "$harness" == \#* ]] && continue
  wanted "$harness" || continue
  if [[ "$harness" != "$current" ]]; then
    printf '\n%s\n' "$harness"
    current="$harness"
  fi
  process "$harness" "$mode" "$src" "$tgt"
done < "$MANIFEST"

printf '\n%s linked, %s already ok, %s skipped, %s need attention' \
  "$n_linked" "$n_ok" "$n_skipped" "$n_conflict"
[[ "$ACTION" == unlink ]] && printf ', %s removed' "$n_removed"
printf '\n'

if (( n_conflict > 0 )) && [[ "$ACTION" == status ]]; then
  echo "Run ./install.sh to link them; real files in the way are backed up first."
fi
