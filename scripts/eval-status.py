#!/usr/bin/env python3
"""Report whether a skill-eval run still matches the current code and runtime.

This command performs no model calls. It recomputes content, runner, and runtime
fingerprints from a run directory (or a promoted baseline with the same manifest
layout).
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Mapping, Optional

from skill_eval_utils import (
    EVAL_PROTOCOL_VERSION,
    build_compliance_record,
    build_trigger_record,
    clean_base_environment,
    command_version,
    default_runner_files,
    measure_profile_runtime,
)


REPO = Path(__file__).resolve().parents[1]
AGENTS_SKILLS = Path.home() / ".agents" / "skills"
COMPONENTS = ("content", "runner", "config", "combined")


def load_manifest(path: Path) -> dict:
    manifest_path = path / "fingerprints.json" if path.is_dir() else path
    if not manifest_path.is_file():
        raise FileNotFoundError(f"fingerprint manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != EVAL_PROTOCOL_VERSION:
        raise ValueError(
            f"unsupported fingerprint schema {manifest.get('schema_version')!r}; "
            f"expected {EVAL_PROTOCOL_VERSION}"
        )
    if manifest.get("runner") not in {"compliance", "trigger"}:
        raise ValueError(f"unknown runner in manifest: {manifest.get('runner')!r}")
    if not isinstance(manifest.get("records"), dict) or not manifest["records"]:
        raise ValueError("fingerprint manifest has no records")
    return manifest


def resolve_skill(name: str) -> Path:
    repo_skill = REPO / "shared" / "skills" / name
    if repo_skill.is_dir():
        return repo_skill
    installed = AGENTS_SKILLS / name
    if installed.is_dir():
        return installed
    raise FileNotFoundError(f"skill not found in repo or agent store: {name}")


def find_compliance_case(record: Mapping, case_id: str) -> dict:
    skill = record["skill"]
    spec = json.loads(
        (REPO / "shared" / "skills" / skill / "evals" / "evals.json").read_text()
    )
    for case in spec.get("evals", []):
        if case.get("id") == case_id:
            return case
    raise KeyError(f"eval case not found: {skill}/{case_id}")


def find_trigger_case(record: Mapping, case_id: str) -> dict:
    skill = record["skill"]
    spec = json.loads(
        (REPO / "shared" / "skills" / skill / "evals" / "evals.json").read_text()
    )
    for probe in spec.get("trigger_probes", []):
        if probe.get("id") == case_id:
            return probe
    raise KeyError(f"trigger probe not found: {skill}/{case_id}")


def current_record(
    runner: str,
    stored: Mapping,
    current_pi_version: str,
    profile_runtime_fingerprint: str,
) -> dict:
    config = {
        **stored["config"],
        "pi_version": current_pi_version,
        "profile_runtime_fingerprint": profile_runtime_fingerprint,
    }
    runner_files = default_runner_files(REPO, runner)
    skill = stored["skill"]
    case_id = stored["case_id"]
    if runner == "compliance":
        eval_spec = find_compliance_case(stored, case_id)
        loaded = {name: resolve_skill(name) for name in stored.get("loaded_skills", [])}
        return build_compliance_record(
            skill,
            resolve_skill(skill),
            eval_spec,
            loaded,
            runner_files,
            config,
        )
    return build_trigger_record(
        skill,
        REPO / "shared" / "skills",
        find_trigger_case(stored, case_id),
        runner_files,
        config,
    )


def classify(stored: Mapping, current: Mapping) -> tuple[str, list[str]]:
    stored_fps = stored.get("fingerprints", {})
    current_fps = current.get("fingerprints", {})
    changed = [
        component
        for component in COMPONENTS
        if stored_fps.get(component) != current_fps.get(component)
    ]
    return ("FRESH" if not changed else "STALE", changed)


def run_completeness(path: Path, manifest: Mapping) -> tuple[list[str], list[str]]:
    """Return (run errors, fingerprinted cases with no result entry).

    Freshness alone is not enough: a run whose calls failed or that stopped
    before writing results matches the current code exactly and would still be
    useless as evidence.
    """
    directory = path if path.is_dir() else path.parent
    errors: list[str] = []
    errors_path = directory / "errors.json"
    if errors_path.is_file():
        recorded = json.loads(errors_path.read_text())
        if isinstance(recorded, list):
            errors = [str(item) for item in recorded]
    results_name = "triggers.json" if manifest["runner"] == "trigger" else "benchmark.json"
    results_path = directory / results_name
    results = {}
    if results_path.is_file():
        loaded = json.loads(results_path.read_text())
        if isinstance(loaded, dict):
            results = loaded
    missing = sorted(key for key in manifest["records"] if key not in results)
    if not results_path.is_file():
        missing = sorted(manifest["records"])
    return errors, missing


def inspect(path: Path) -> dict:
    manifest = load_manifest(path)
    runner = manifest["runner"]
    pi_version = command_version("pi")
    profile_name = "eval" if runner == "compliance" else "probe"
    with tempfile.TemporaryDirectory(prefix="skill-eval-status-") as tempdir:
        profile_runtime = measure_profile_runtime(
            Path(tempdir) / "profile",
            clean_base_environment(),
            profile_name=profile_name,
        )
        entries = []
        for key, stored in sorted(manifest["records"].items()):
            try:
                current = current_record(
                    runner,
                    stored,
                    pi_version,
                    profile_runtime,
                )
                status, changed = classify(stored, current)
                reason = None
            except (FileNotFoundError, KeyError, TypeError, ValueError) as exc:
                status = "MISSING"
                changed = []
                reason = str(exc)
            entries.append(
                {
                    "key": key,
                    "status": status,
                    "changed": changed,
                    "reason": reason,
                }
            )
    counts = {
        status: sum(entry["status"] == status for entry in entries)
        for status in ("FRESH", "STALE", "MISSING")
    }
    run_errors, missing_results = run_completeness(path, manifest)
    return {
        "schema_version": EVAL_PROTOCOL_VERSION,
        "runner": runner,
        "pi_version": pi_version,
        "profile_runtime_fingerprint": profile_runtime,
        "counts": counts,
        "entries": entries,
        "run_errors": run_errors,
        "missing_results": missing_results,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="run directory or fingerprints.json")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 unless every case is fresh",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        report = inspect(args.path)
    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
        RuntimeError,
    ) as exc:
        if args.json:
            print(json.dumps({"status": "ERROR", "reason": str(exc)}, indent=2))
        else:
            print(f"ERROR {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for entry in report["entries"]:
            detail = ""
            if entry["changed"]:
                detail = f" ({', '.join(entry['changed'])})"
            elif entry["reason"]:
                detail = f" ({entry['reason']})"
            print(f"{entry['status']:7} {entry['key']}{detail}")
        counts = report["counts"]
        print(
            f"{counts['FRESH']} fresh, {counts['STALE']} stale, "
            f"{counts['MISSING']} missing"
        )
        for error in report["run_errors"]:
            print(f"ERROR   {error}")
        for key in report["missing_results"]:
            print(f"NORESULT {key} (fingerprinted but absent from results)")

    if args.check:
        if any(entry["status"] != "FRESH" for entry in report["entries"]):
            return 1
        if report["run_errors"] or report["missing_results"]:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
