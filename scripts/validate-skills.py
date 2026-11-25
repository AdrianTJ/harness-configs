#!/usr/bin/env python3
"""Check every SKILL.md against the Agent Skills spec (agentskills.io).

`name` matches its parent directory, uses only lowercase alphanumerics and
single hyphens, and is 1-64 chars; `description` is present and <= 1024 chars.
Exit 0 only if every skill passes.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "shared" / "skills"
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def field(front: str, key: str) -> str:
    """Value of a top-level frontmatter key, joining YAML folded (>) continuations."""
    lines = front.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            value = line[len(key) + 1:].strip()
            if value in (">", "|", ">-", "|-"):
                cont = []
                for nxt in lines[i + 1:]:
                    if nxt and not nxt[0].isspace():
                        break
                    cont.append(nxt.strip())
                value = " ".join(c for c in cont if c)
            return value
    return ""


def check(skill_md: Path) -> list:
    text = skill_md.read_text()
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        return ["missing YAML frontmatter"]
    front = text[4:text.index("\n---", 4)]
    errors = []
    name, desc = field(front, "name"), field(front, "description")
    if name != skill_md.parent.name:
        errors.append(f"name {name!r} does not match directory {skill_md.parent.name!r}")
    if not NAME_RE.match(name) or not 1 <= len(name) <= 64:
        errors.append(f"name {name!r} is not 1-64 lowercase alphanumerics with single hyphens")
    if not desc:
        errors.append("description is missing")
    elif len(desc) > 1024:
        errors.append(f"description is {len(desc)} chars (max 1024)")
    return errors


def main() -> int:
    failed = False
    for skill_md in sorted(SKILLS.glob("*/SKILL.md")):
        errors = check(skill_md)
        rel = skill_md.relative_to(ROOT)
        if errors:
            failed = True
            for e in errors:
                print(f"FAIL {rel}: {e}", file=sys.stderr)
        else:
            print(f"OK   {rel}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
