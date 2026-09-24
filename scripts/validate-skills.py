#!/usr/bin/env python3
"""Validate this repo's skills and their eval specs.

Two things, both free and fast enough to run on every commit (and in CI):

  1. Every SKILL.md conforms to the Agent Skills spec (agentskills.io):
     `name` matches its parent directory, uses only lowercase alphanumerics and
     single hyphens, is 1-64 chars; `description` is present and <= 1024 chars.
  2. Every evals/evals.json is well formed: valid JSON, `skill_name` matches
     the containing skill, each eval has a unique `id` and a `prompt`,
     `assertions` and optional `transcript_assertions` are non-empty lists of
     strings, and every path in `files` resolves relative to the skill.

Scoring the evals against a real model is a separate, by-eye step — see
"Skill evals" in shared/README.md. This only checks that the specs are
structurally sound, so a malformed one fails here rather than mid-review.

Exit 0 only if everything passes. No arguments; repo root is derived from this
file's location (scripts/ -> repo root one level up).
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOTS = [REPO_ROOT / "shared" / "skills"]
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def frontmatter(text: str) -> str:
    """Return the YAML frontmatter block, or '' if the file has none."""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def check_skill(skill_md: Path) -> list:
    errors = []
    fm = frontmatter(skill_md.read_text())
    if not fm:
        return ["no YAML frontmatter"]

    name_m = re.search(r"^name:[ \t]*(.+)$", fm, re.M)
    name = name_m.group(1).strip() if name_m else None
    parent = skill_md.parent.name

    if not name:
        errors.append("missing 'name'")
    else:
        if name != parent:
            errors.append(f"name {name!r} != directory {parent!r} (spec requires they match)")
        if not NAME_RE.match(name):
            errors.append(f"name {name!r} must be lowercase alphanumerics separated by single hyphens")
        if not 1 <= len(name) <= 64:
            errors.append(f"name is {len(name)} chars, must be 1-64")

    desc_m = re.search(r"^description:[ \t]*>?[ \t]*\n?((?:.|\n)*?)(?=\n[a-z][a-z-]*:|\Z)", fm, re.M)
    if not desc_m:
        errors.append("missing 'description'")
    else:
        desc = " ".join(desc_m.group(1).split())
        if not desc:
            errors.append("'description' is empty")
        elif len(desc) > 1024:
            errors.append(f"description is {len(desc)} chars, spec caps it at 1024")

    return errors


def fixture_fields(entry) -> tuple:
    if isinstance(entry, str):
        return entry, None
    if not isinstance(entry, dict):
        return None, "fixture entry must be a string or object"
    source = entry.get("source")
    destination = entry.get("dest")
    if not isinstance(source, str) or not source.strip():
        return None, "fixture object requires a non-empty 'source'"
    if not isinstance(destination, str) or not destination.strip():
        return None, "fixture object requires a non-empty 'dest'"
    source_path = Path(source)
    destination_path = Path(destination)
    if source_path.is_absolute() or ".." in source_path.parts:
        return None, f"fixture source must stay inside the skill: {source}"
    if destination_path.is_absolute() or ".." in destination_path.parts:
        return None, f"fixture destination must stay inside the arm: {destination}"
    return source, None


def check_evals(evals_json: Path) -> list:
    errors = []
    skill_dir = evals_json.parent.parent
    try:
        spec = json.loads(evals_json.read_text())
    except json.JSONDecodeError as exc:
        return [f"not valid JSON: {exc}"]

    if not isinstance(spec, dict):
        return ["top level must be an object"]

    if spec.get("skill_name") != skill_dir.name:
        errors.append(f"skill_name {spec.get('skill_name')!r} != skill directory {skill_dir.name!r}")

    evals = spec.get("evals")
    if not isinstance(evals, list) or not evals:
        return errors + ["'evals' must be a non-empty array"]

    seen = set()
    for i, ev in enumerate(evals):
        where = f"evals[{i}]"
        if not isinstance(ev, dict):
            errors.append(f"{where}: must be an object")
            continue
        eid = ev.get("id")
        if not eid:
            errors.append(f"{where}: missing 'id'")
        elif eid in seen:
            errors.append(f"{where}: duplicate id {eid!r}")
        else:
            seen.add(eid)
        if not ev.get("prompt"):
            errors.append(f"{where}: missing 'prompt'")

        assertions = ev.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            errors.append(f"{where}: 'assertions' must be a non-empty array")
        elif not all(isinstance(a, str) and a.strip() for a in assertions):
            errors.append(f"{where}: every assertion must be a non-empty string")

        setup = ev.get("setup")
        if setup is not None:
            if not isinstance(setup, list) or not setup:
                errors.append(f"{where}: 'setup' must be a non-empty array")
            elif not all(isinstance(command, str) and command.strip() for command in setup):
                errors.append(f"{where}: every setup command must be a non-empty string")

        process_assertions = ev.get("transcript_assertions")
        if process_assertions is not None:
            if not isinstance(process_assertions, list) or not process_assertions:
                errors.append(
                    f"{where}: 'transcript_assertions' must be a non-empty array"
                )
            elif not all(
                isinstance(a, str) and a.strip() for a in process_assertions
            ):
                errors.append(
                    f"{where}: every transcript assertion must be a non-empty string"
                )

        for fixture in ev.get("files") or []:
            source, error = fixture_fields(fixture)
            if error:
                errors.append(f"{where}: {error}")
            elif not (skill_dir / source).exists():
                errors.append(f"{where}: file not found: {source}")

    for i, tp in enumerate(spec.get("trigger_probes") or []):
        where = f"trigger_probes[{i}]"
        if not isinstance(tp, dict):
            errors.append(f"{where}: must be an object")
            continue
        tid = tp.get("id")
        if not tid:
            errors.append(f"{where}: missing 'id'")
        elif tid in seen:
            errors.append(f"{where}: duplicate id {tid!r} (collides with an eval id)")
        else:
            seen.add(tid)
        prompt = tp.get("prompt") or ""
        if not prompt.strip():
            errors.append(f"{where}: missing 'prompt'")
            continue
        expect_activation = tp.get("expect_activation", True)
        if not isinstance(expect_activation, bool):
            errors.append(f"{where}: 'expect_activation' must be boolean")
        for fixture in tp.get("files") or []:
            source, error = fixture_fields(fixture)
            if error:
                errors.append(f"{where}: {error}")
            elif not (skill_dir / source).exists():
                errors.append(f"{where}: file not found: {source}")

        fps = tp.get("fingerprints")
        if not isinstance(fps, list) or not fps or not all(isinstance(f, str) and f.strip() for f in fps):
            errors.append(f"{where}: 'fingerprints' must be a non-empty array of strings")
            continue
        else:
            lowering = prompt.lower()
            own_text = (skill_dir / "SKILL.md").read_text().lower()
            others = []
            for other in sorted(skill_dir.parent.glob("*/SKILL.md")):
                if other.parent != skill_dir:
                    others.append(other.read_text().lower())
            for f in fps:
                fl = f.lower()
                if fl in lowering:
                    errors.append(f"{where}: fingerprint {f!r} leaks into the prompt (false positive)")
                if len(f) < 4:
                    errors.append(f"{where}: fingerprint {f!r} too short to be distinctive")
                if fl not in own_text:
                    errors.append(f"{where}: fingerprint {f!r} never appears in its own SKILL.md (can never legitimately fire)")
                if any(fl in o for o in others):
                    errors.append(f"{where}: fingerprint {f!r} also appears in another skill (control cannot distinguish)")

    return errors


def main() -> int:
    skill_mds = []
    for root in SKILLS_ROOTS:
        if root.is_dir():
            skill_mds += sorted(root.glob("*/SKILL.md"))
    if not skill_mds:
        print("no skills found under " + ", ".join(
            str(r.relative_to(REPO_ROOT)) for r in SKILLS_ROOTS), file=sys.stderr)
        return 1

    failed = False
    for skill_md in skill_mds:
        rel = skill_md.relative_to(REPO_ROOT)
        errors = check_skill(skill_md)

        evals_json = skill_md.parent / "evals" / "evals.json"
        if evals_json.exists():
            errors += [f"evals.json: {e}" for e in check_evals(evals_json)]
        else:
            errors.append("no evals/evals.json (every skill should have at least one eval)")

        if errors:
            failed = True
            print(f"FAIL {rel}")
            for err in errors:
                print(f"     - {err}")
        else:
            print(f"OK   {rel}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
