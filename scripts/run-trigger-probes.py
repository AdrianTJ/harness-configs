#!/usr/bin/env python3
"""Measure whether automatically selectable skills route on realistic prompts.

Linked and control arms receive independent disposable profiles, HOME/XDG roots,
skill catalogs, and workspaces. Pi runs in JSON event mode so trigger results
retain output fingerprints, read/tool evidence, environment manifests, usage,
and observed models. Raw runs live under gitignored eval-runs/ and include a
per-case fingerprint manifest.
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from eval_scoring import trigger_metrics
from pi_eval_client import require_success, run_pi, write_run_evidence
from skill_eval_utils import (
    EVAL_PROTOCOL_VERSION,
    build_trigger_record,
    clean_base_environment,
    command_version,
    create_isolated_profile,
    default_runner_files,
    install_skill_copies,
    measure_profile_runtime,
    prepare_isolated_arms,
    write_fingerprint_manifest,
)

REPO = Path(__file__).resolve().parents[1]
PROVIDER = os.environ.get("EVAL_PROVIDER", "opencode-go")
MODEL = os.environ.get("EVAL_MODEL", "muse-spark-1.3-contributor")
CALL_TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "600"))
DEFAULT_REPS = 5


def repo_snapshot() -> str:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"tripwire blind: git status failed: {completed.stderr.strip()[-200:]}"
        )
    return completed.stdout


def hit(output: str, fingerprints: list[str]) -> list[str]:
    lowered = output.lower()
    return [value for value in fingerprints if value.lower() in lowered]


def read_target_skill(result, skill: str) -> bool:
    for path in result.files_read:
        parts = Path(path).parts
        if len(parts) >= 2 and parts[-2] == skill and parts[-1] == "SKILL.md":
            return True
    return False


def main() -> int:
    pairs = sys.argv[1:]
    plan = []
    if pairs:
        for pair in pairs:
            target, _, reps = pair.partition("=")
            skill, separator, probe_id = target.partition("/")
            if not skill or (separator and not probe_id):
                raise ValueError(f"invalid trigger target: {target}")
            plan.append(
                (
                    skill,
                    probe_id if separator else None,
                    int(reps or DEFAULT_REPS),
                )
            )
    else:
        for skill_dir in sorted((REPO / "shared" / "skills").iterdir()):
            spec_file = skill_dir / "evals" / "evals.json"
            if not spec_file.exists():
                continue
            spec = json.loads(spec_file.read_text())
            if spec.get("trigger_probes"):
                plan.append((skill_dir.name, None, DEFAULT_REPS))
    if not plan:
        print("no skills with trigger_probes; nothing to do")
        return 0

    trit = Path(tempfile.mkdtemp(prefix="trigger-probes-"))
    base_env = clean_base_environment()
    base_work = trit / "work"
    profile_runtime = measure_profile_runtime(
        trit / "fingerprint-profile", base_env, profile_name="probe"
    )
    iteration = (
        REPO
        / "eval-runs"
        / os.environ.get("EVAL_ITERATION", "iteration-1")
        / "triggers"
    )
    results: dict[str, dict] = {}
    errors: list[str] = []
    calls = 0
    fingerprint_records: dict[str, dict] = {}
    clean_tree = repo_snapshot()
    pi_version = command_version("pi")
    runner_files = default_runner_files(REPO, "trigger")

    for skill, selected_probe, reps in plan:
        spec = json.loads(
            (REPO / "shared" / "skills" / skill / "evals" / "evals.json").read_text()
        )
        probes = spec.get("trigger_probes", [])
        if selected_probe:
            probes = [probe for probe in probes if probe.get("id") == selected_probe]
            if not probes:
                raise ValueError(f"trigger probe not found: {skill}/{selected_probe}")
        config = {
            "provider": PROVIDER,
            "model": MODEL,
            "pi_version": pi_version,
            "profile_runtime_fingerprint": profile_runtime,
            "timeout_seconds": CALL_TIMEOUT,
            "repetitions": reps,
        }
        for probe in probes:
            key = f"{skill}/{probe['id']}"
            fingerprint_records[key] = build_trigger_record(
                skill,
                REPO / "shared" / "skills",
                probe,
                runner_files,
                config,
            )
            hits = 0
            control_hits = 0
            skill_reads = 0
            control_skill_reads = 0
            observed_models: set[str] = set()

            for rep in range(1, reps + 1):
                result_dir = iteration / skill / probe["id"] / f"rep{rep}"
                result_dir.mkdir(parents=True, exist_ok=True)
                try:
                    arms = prepare_isolated_arms(
                        base_work / skill / probe["id"] / f"rep{rep}",
                        REPO / "shared" / "skills" / skill,
                        probe.get("files") or [],
                        ("linked", "control"),
                        profile_name="probe",
                    )
                    arm_envs = {
                        name: create_isolated_profile(arm, base_env)
                        for name, arm in arms.items()
                    }
                    install_skill_copies(
                        arms["linked"].profile_dir,
                        REPO / "shared" / "skills",
                    )
                    install_skill_copies(
                        arms["control"].profile_dir,
                        REPO / "shared" / "skills",
                        exclude={skill},
                    )

                    linked_result = run_pi(
                        PROVIDER,
                        MODEL,
                        [probe["prompt"]],
                        arms["linked"].workdir,
                        arm_envs["linked"],
                        CALL_TIMEOUT,
                    )
                    calls += 1
                    write_run_evidence(
                        result_dir / "linked-evidence",
                        linked_result,
                        arms["linked"],
                    )
                    require_success(linked_result)
                    control_result = run_pi(
                        PROVIDER,
                        MODEL,
                        [probe["prompt"]],
                        arms["control"].workdir,
                        arm_envs["control"],
                        CALL_TIMEOUT,
                    )
                    calls += 1
                    write_run_evidence(
                        result_dir / "control-evidence",
                        control_result,
                        arms["control"],
                    )
                    require_success(control_result)
                    (result_dir / "linked.txt").write_text(linked_result.output)
                    (result_dir / "control.txt").write_text(control_result.output)

                    linked_match = hit(linked_result.output, probe["fingerprints"])
                    control_match = hit(control_result.output, probe["fingerprints"])
                    hits += bool(linked_match)
                    control_hits += bool(control_match)
                    linked_read = read_target_skill(linked_result, skill)
                    control_read = read_target_skill(control_result, skill)
                    skill_reads += linked_read
                    control_skill_reads += control_read
                    if linked_result.model:
                        observed_models.add(linked_result.model)
                    if control_result.model:
                        observed_models.add(control_result.model)

                    if repo_snapshot() != clean_tree:
                        raise RuntimeError(
                            "SANDBOX BREACH during trigger probe rep; inspect git status"
                        )
                    print(
                        f"OK   {key} rep{rep}: "
                        f"linked={'Y' if linked_match else '-'} "
                        f"control={'Y' if control_match else '-'} "
                        f"skill_read={'Y' if linked_read else '-'}"
                    )
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{key} rep{rep}: {exc}")
                    print(f"FAIL {key} rep{rep}: {exc}")

            results[key] = trigger_metrics(
                reps=reps,
                expect_activation=probe.get("expect_activation", True),
                fingerprint_hits=hits,
                control_fingerprint_hits=control_hits,
                skill_reads=skill_reads,
                control_skill_reads=control_skill_reads,
            )
            results[key]["observed_models"] = sorted(observed_models)

    write_fingerprint_manifest(
        iteration / "fingerprints.json", "trigger", fingerprint_records
    )
    (iteration / "meta.json").write_text(
        json.dumps(
            {
                "date": datetime.now(timezone.utc).isoformat(),
                "provider": PROVIDER,
                "model": MODEL,
                "pi_version": pi_version,
                "profile_runtime_fingerprint": profile_runtime,
                "plan": plan,
                "calls": calls,
                "fingerprint_schema_version": EVAL_PROTOCOL_VERSION,
                "fingerprints": "fingerprints.json",
                "repo": subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=REPO,
                ).stdout.strip(),
                "repo_dirty": bool(clean_tree),
            },
            indent=2,
        )
        + "\n"
    )
    (iteration / "triggers.json").write_text(json.dumps(results, indent=2) + "\n")
    (iteration / "errors.json").write_text(json.dumps(errors, indent=2) + "\n")

    print(f"\n{len(results)} probes, {calls} calls, {len(errors)} errors")
    for key, result in results.items():
        print(
            f"  {key}: trigger {result['trigger_rate']:.0%}, "
            f"control {result['control_rate']:.0%}, "
            f"lift {result['lift']:+.0%}, "
            f"skill read {result['linked_skill_read_rate']:.0%}"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
