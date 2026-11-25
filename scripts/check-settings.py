#!/usr/bin/env python3
"""Keep tool-injected config out of the tracked harness settings.

Terminal apps and agent managers (Orca, herdr, cmux, Paseo, ...) rewrite the
settings files this repo symlinks, so their additions land in `git diff` here.
A hand-written settings file is well under the size cap; injected boilerplate
blows past it, and known app names should never appear in it.
"""
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_SETTINGS_BYTES = 8192
APP_NAMES = re.compile(r"orca|herdr|cmux|paseo", re.IGNORECASE)
SETTINGS = ["pi/settings.json"]


def main() -> int:
    errors = []
    for rel in SETTINGS:
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text()
        if len(text.encode()) > MAX_SETTINGS_BYTES:
            errors.append(f"{rel}: {len(text.encode())} bytes, over the {MAX_SETTINGS_BYTES}-byte cap (app-injected config?)")
        if APP_NAMES.search(text):
            errors.append(f"{rel}: mentions an app that injects config ({APP_NAMES.search(text).group(0)})")
    for e in errors:
        print(f"FAIL {e}", file=sys.stderr)
    if not errors:
        print("OK   tracked settings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
