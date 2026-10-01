#!/usr/bin/env bash
# Exercises claude-code/hooks/block-dangerous-git.sh: each command must be
# blocked (exit 2) or allowed (exit 0) as listed.
set -euo pipefail
cd "$(dirname "$0")/.."

HOOK=claude-code/hooks/block-dangerous-git.sh
fail=0

check() {
  local want=$1 cmd=$2 got=0
  jq -n --arg c "$cmd" '{tool_name:"Bash",tool_input:{command:$c}}' | bash "$HOOK" >/dev/null 2>&1 || got=$?
  if [ "$got" != "$want" ]; then
    printf 'FAIL want=%s got=%s: %s\n' "$want" "$got" "$cmd" >&2
    fail=1
  fi
}

for c in 'git push' 'git push --force origin main' 'git push -f' 'git push origin +main' \
         'git  push -f' $'git\tpush' 'git -C /x push' 'git -c a=b push origin main' \
         'cd x && git -C y push --force' 'git reset --hard' 'git reset  --hard HEAD~1' \
         'git reset HEAD~1 --hard' 'git clean -fd' 'git clean -xfd' 'git -C x clean -f' \
         'git branch -D x' 'git checkout .' 'git restore .'; do
  check 2 "$c"
done

for c in 'git status' 'git diff --stat' 'git log --oneline' 'git commit -m "push the button"' \
         'git reset --soft HEAD~1' 'git checkout main' 'git branch -d x' 'git -C /x status' \
         'git clean -n' 'ls'; do
  check 0 "$c"
done

echo '{"tool_name":"Bash","tool_input":{}}' | bash "$HOOK" >/dev/null 2>&1 && { echo "FAIL: empty command allowed" >&2; fail=1; }

exit "$fail"
