#!/usr/bin/env python3
"""Keep tool-injected config out of the tracked harness settings.

Terminal apps and agent managers (Orca, herdr, cmux, ...) rewrite the settings
files this repo symlinks, so their hooks land in `git diff` here. Two rules catch
that without naming any app:

1. Every `$HOME/.claude/hooks/<script>` a settings hook calls must be tracked in
   claude-code/hooks/, so a hook can never point at an app-managed script.
2. Settings files stay small. A hand-written settings.json is well under the cap;
   injected boilerplate blows past it.

The app list is a second line of defence, scanned only in the machine-readable
config (settings, extensions, plugins), never in the prose docs.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_SETTINGS_BYTES = 8192
APP_NAMES = re.compile(r"orca|herdr|cmux", re.IGNORECASE)
HOOK_REF = re.compile(r"\.claude/hooks/([A-Za-z0-9_.-]+)")
SETTINGS = ["claude-code/settings.json", "pi/settings.json", "opencode/opencode.json"]
SCANNED_DIRS = ["pi/extensions", "omp/extensions", "opencode/plugin"]


def hook_commands(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "command" and isinstance(value, str):
                yield value
            else:
                yield from hook_commands(value)
    elif isinstance(node, list):
        for item in node:
            yield from hook_commands(item)


def main(root=ROOT):
    errors = []
    tracked_hooks = {p.name for p in (root / "claude-code/hooks").glob("*") if p.is_file()}
    for rel in SETTINGS:
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text()
        if len(text.encode()) > MAX_SETTINGS_BYTES:
            errors.append(f"{rel}: {len(text.encode())} bytes exceeds {MAX_SETTINGS_BYTES}; app-injected config?")
        if APP_NAMES.search(text):
            errors.append(f"{rel}: mentions an app-managed tool ({APP_NAMES.pattern})")
        if rel == "claude-code/settings.json":
            data = json.loads(text)
            if "statusLine" in data:
                errors.append(f"{rel}: statusLine is app-managed; keep it out of the tracked file")
            for command in hook_commands(data.get("hooks", {})):
                for script in HOOK_REF.findall(command):
                    if script not in tracked_hooks:
                        errors.append(f"{rel}: hook calls untracked script {script}")
    for rel in SCANNED_DIRS:
        for path in (root / rel).glob("*"):
            if path.is_file() and path.name != ".gitkeep" and APP_NAMES.search(path.name):
                errors.append(f"{path.relative_to(root)}: app-managed file name")
    for err in errors:
        print(err, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
