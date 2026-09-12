#!/usr/bin/env bash
# check-upstream.sh — report pinned upstreams that moved since the SOURCES.md pins.
#
# Report-only by design: refreshing a vendored or adapted skill means
# re-applying the adaptation by hand (see SOURCES.md Rules), so this script
# never writes anything. It exits 1 when a pin is stale, with the refresh
# pointer next to each line. Runs weekly in CI; run it manually any time.
#
# Pins below mirror SOURCES.md. Update both when refreshing.
set -u

stale=0

check_git() { # name, url, ref, pinned-prefix
  local name="$1" url="$2" ref="$3" pin="$4" head
  head=$(git ls-remote "$url" "$ref" 2>/dev/null | awk '{print $1}')
  if [[ -z "$head" ]]; then
    stale=1; printf 'ERROR   %s\n  could not resolve %s %s\n' "$name" "$url" "$ref"; return
  fi
  if [[ "$head" == "$pin"* ]]; then printf 'OK      %s (%s)\n' "$name" "$pin"
  else stale=1; printf 'STALE   %s\n  pinned: %s  upstream: %s\n' "$name" "$pin" "$head"; fi
}

check_npm() { # name, pinned-version
  local name="$1" pin="$2" cur
  cur=$(npm view "$name" version 2>/dev/null)
  if [[ -z "$cur" ]]; then
    stale=1; printf 'ERROR   %s\n  npm view failed\n' "$name"; return
  fi
  if [[ "$cur" == "$pin" ]]; then printf 'OK      %s (%s)\n' "$name" "$pin"
  else stale=1; printf 'STALE   %s\n  pinned: %s  upstream: %s\n' "$name" "$pin" "$cur"; fi
}

echo "== git pins =="
check_git "pro-workflow (deslop upstream)" https://github.com/rohitg00/pro-workflow HEAD 7f7209d
check_git "engineering-discipline (deslop upstream)" https://github.com/tmdgusya/engineering-discipline HEAD 137dead
check_git "bro-skills" https://github.com/eukosh/bro-skills refs/heads/main 08d2e07
check_git "superpowers (brainstorming upstream)" https://github.com/obra/superpowers HEAD b36e0829
check_git "pi-profiles (profile-badge upstream)" https://github.com/AdrianTJ/pi-profiles HEAD df7dbc0

echo "== npm pins (pi packages) =="
check_npm "@dietrichgebert/ponytail" 4.9.0
check_npm "pi-subagents-lite" 1.13.1
check_npm "@bacnh85/pi-fff" 0.8.0
check_npm "@jqwn/pi-ask-user-question" 0.2.0
check_npm "@narumitw/pi-btw" 0.58.1
check_npm "pi-tasks" 0.2.7
check_npm "pi-web-lite" 0.1.6

echo
if (( stale > 0 )); then
  echo "Pins moved upstream — refresh per SOURCES.md, then update pins here and there."
  exit 1
fi
echo "All pins hold."
