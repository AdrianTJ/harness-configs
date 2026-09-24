#!/usr/bin/env python3
"""Run forced-load A/B skill compliance evals through Pi.

Each treatment, control, and judge attempt gets a fresh workspace, HOME/XDG
root, and Pi profile. Pi runs in JSON event mode, so every result retains the
final response, transcript/tool evidence, environment manifest, usage, and
observed model. Scored runs write deterministic per-case fingerprints and
remain under gitignored eval-runs/ unless explicitly reviewed and promoted.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from eval_scoring import aggregate_reps, parse_judge_verdict
from pi_eval_client import require_success, run_pi, run_setup, write_run_evidence
from skill_eval_utils import (
    EVAL_PROTOCOL_VERSION,
    build_compliance_record,
    clean_base_environment,
    command_version,
    create_isolated_profile,
    default_runner_files,
    measure_profile_runtime,
    prepare_isolated_arms,
    write_fingerprint_manifest,
)

REPO = Path(__file__).resolve().parents[1]
PROVIDER = os.environ.get("EVAL_PROVIDER", "opencode-go")
MODEL = os.environ.get("EVAL_MODEL", "muse-spark-1.3-contributor")
JUDGE_PROVIDER = os.environ.get("EVAL_JUDGE_PROVIDER")
JUDGE_MODEL = os.environ.get("EVAL_JUDGE_MODEL")
ALLOW_SELF_JUDGE = os.environ.get("EVAL_ALLOW_SELF_JUDGE") == "1"
CALL_TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "600"))
PILOT = {"deslop": 6, "write-skill": 3}

JUDGE_TEMPLATE = """You are an independent evaluator comparing two anonymous Pi runs. Do not guess which run received a skill.

Evidence for side A is under A/. Evidence for side B is under B/. Each side contains:
- events.jsonl: raw Pi JSON event stream
- transcript.json: final output, usage, tool calls, files read/modified, commands, and errors
- environment.json: hashed workspace, HOME, and profile manifests (credentials excluded)

Inspect the evidence with your tools. Judge observable behavior, not wording. Never reward a claim that the evidence contradicts.

User request:
{prompt}

OUTPUT ASSERTIONS: {output_count}
{output_assertions}

PROCESS ASSERTIONS: {process_count}
{process_assertions}

For every numbered output and process assertion, write PASS or FAIL for side A and side B, followed by a short exact quote or evidence path. Then end with exactly these lines and nothing after them:
A-OUTPUT: <passed output assertions>
A-PROCESS: <passed process assertions>
A-PASS: <total passed assertions>
B-OUTPUT: <passed output assertions>
B-PROCESS: <passed process assertions>
B-PASS: <total passed assertions>
"""


def require_independent_judge() -> None:
    if not JUDGE_PROVIDER or not JUDGE_MODEL:
        raise RuntimeError(
            "EVAL_JUDGE_PROVIDER and EVAL_JUDGE_MODEL are required; "
            "pin the judge explicitly for comparable results"
        )
    if (
        JUDGE_PROVIDER == PROVIDER
        and JUDGE_MODEL == MODEL
        and not ALLOW_SELF_JUDGE
    ):
        raise RuntimeError(
            "judge and target are the same provider/model; choose an independent "
            "judge or set EVAL_ALLOW_SELF_JUDGE=1 for an explicitly exploratory run"
        )


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


def load_evals(skill: str) -> list[dict]:
    spec = json.loads(
        (REPO / "shared" / "skills" / skill / "evals" / "evals.json").read_text()
    )
    if spec["skill_name"] != skill:
        raise ValueError(f"skill_name mismatch in {skill}")
    return spec["evals"]


def numbered(items: list[str], empty: str) -> str:
    if not items:
        return empty
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, 1))


def stage_judge_evidence(
    result_dir: Path,
    judge_arms: list,
    sides: dict[str, tuple],
) -> None:
    for label, (run_result, arm) in sides.items():
        source = result_dir / f"{label}-evidence"
        write_run_evidence(source, run_result, arm)
        for judge_arm in judge_arms:
            shutil.copytree(source, judge_arm.workdir / label)


def grade(
    prompt: str,
    output_assertions: list[str],
    process_assertions: list[str],
    judge_arms: list,
    judge_envs: list[dict],
) -> tuple[dict, object, object]:
    judge_prompt = JUDGE_TEMPLATE.format(
        prompt=prompt,
        output_count=len(output_assertions),
        output_assertions=numbered(output_assertions, "(none)"),
        process_count=len(process_assertions),
        process_assertions=numbered(process_assertions, "(none)"),
    )
    last_result = None
    last_error = ""
    for arm, env in zip(judge_arms, judge_envs):
        last_result = run_pi(
            JUDGE_PROVIDER,
            JUDGE_MODEL,
            ["--no-skills", judge_prompt],
            arm.workdir,
            env,
            CALL_TIMEOUT,
        )
        try:
            require_success(last_result)
            return parse_judge_verdict(
                last_result.output,
                output_assertions=len(output_assertions),
                process_assertions=len(process_assertions),
            ), last_result, arm
        except (ValueError, RuntimeError) as exc:
            last_error = str(exc)
    raise RuntimeError(
        "judge verdict invalid after isolated retries: "
        f"{last_error}; output tail: {(last_result.output if last_result else '')[-300:]}"
    )


def main() -> int:
    require_independent_judge()
    pairs = sys.argv[1:] or [f"{skill}={reps}" for skill, reps in PILOT.items()]
    plan = []
    for pair in pairs:
        target, _, reps = pair.partition("=")
        skill, separator, case_id = target.partition("/")
        if not skill or (separator and not case_id):
            raise ValueError(f"invalid eval target: {target}")
        plan.append(
            (skill, case_id if separator else None, int(reps or PILOT.get(skill, 1)))
        )

    trit = Path(tempfile.mkdtemp(prefix="skill-evals-"))
    base_env = clean_base_environment()
    iteration = REPO / "eval-runs" / os.environ.get("EVAL_ITERATION", "iteration-1")
    base_work = trit / "work"
    profile_runtime = measure_profile_runtime(
        trit / "fingerprint-profile", base_env, profile_name="eval"
    )
    results: dict[str, dict] = {}
    errors: list[str] = []
    calls = 0
    fingerprint_records: dict[str, dict] = {}
    clean_tree = repo_snapshot()
    pi_version = command_version("pi")
    runner_files = default_runner_files(REPO, "compliance")

    for skill, selected_case, reps in plan:
        evals = load_evals(skill)
        if selected_case:
            evals = [case for case in evals if case.get("id") == selected_case]
            if not evals:
                raise ValueError(f"eval case not found: {skill}/{selected_case}")
        loads = [skill] + sorted(
            {name for case in evals for name in case.get("also_load", [])}
        )
        skill_sources: dict[str, Path] = {}
        for name in loads:
            for root in (
                REPO / "shared" / "skills",
                Path.home() / ".agents" / "skills",
            ):
                if (root / name).is_dir():
                    skill_sources[name] = root / name
                    break
            else:
                raise RuntimeError(f"also_load skill not found: {name}")

        skill_source = skill_sources[skill]
        config = {
            "provider": PROVIDER,
            "model": MODEL,
            "judge_provider": JUDGE_PROVIDER,
            "judge_model": JUDGE_MODEL,
            "pi_version": pi_version,
            "profile_runtime_fingerprint": profile_runtime,
            "timeout_seconds": CALL_TIMEOUT,
            "repetitions": reps,
        }
        loaded_sources = {
            name: source for name, source in skill_sources.items() if name != skill
        }

        for case in evals:
            key = f"{skill}/{case['id']}"
            fingerprint_records[key] = build_compliance_record(
                skill,
                skill_source,
                case,
                loaded_sources,
                runner_files,
                config,
            )
            rep_results = []
            output_assertions = list(case.get("assertions") or [])
            process_assertions = list(case.get("transcript_assertions") or [])

            for rep in range(1, reps + 1):
                result_dir = iteration / skill / case["id"] / f"rep{rep}"
                result_dir.mkdir(parents=True, exist_ok=True)
                try:
                    arms = prepare_isolated_arms(
                        base_work / skill / case["id"] / f"rep{rep}",
                        skill_source,
                        case.get("files") or [],
                        ("treatment", "control", "judge-1", "judge-2"),
                        profile_name="eval",
                    )
                    load_flags = []
                    for name, source in skill_sources.items():
                        destination = arms["treatment"].root / "loaded-skills" / name
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(source, destination)
                        load_flags += ["--skill", str(destination)]

                    arm_envs = {
                        name: create_isolated_profile(arm, base_env)
                        for name, arm in arms.items()
                    }
                    for arm_name in ("treatment", "control"):
                        run_setup(
                            case.get("setup") or [],
                            arms[arm_name].workdir,
                            arm_envs[arm_name],
                            CALL_TIMEOUT,
                        )
                    with_result = run_pi(
                        PROVIDER,
                        MODEL,
                        ["--no-skills", *load_flags, case["prompt"]],
                        arms["treatment"].workdir,
                        arm_envs["treatment"],
                        CALL_TIMEOUT,
                    )
                    calls += 1
                    write_run_evidence(
                        result_dir / "with-evidence",
                        with_result,
                        arms["treatment"],
                    )
                    require_success(with_result)
                    without_result = run_pi(
                        PROVIDER,
                        MODEL,
                        ["--no-skills", case["prompt"]],
                        arms["control"].workdir,
                        arm_envs["control"],
                        CALL_TIMEOUT,
                    )
                    calls += 1
                    write_run_evidence(
                        result_dir / "without-evidence",
                        without_result,
                        arms["control"],
                    )
                    require_success(without_result)
                    (result_dir / "with.txt").write_text(with_result.output)
                    (result_dir / "without.txt").write_text(without_result.output)

                    if rep % 2 == 1:
                        sides = {
                            "A": (with_result, arms["treatment"]),
                            "B": (without_result, arms["control"]),
                        }
                        a_is_with = True
                    else:
                        sides = {
                            "A": (without_result, arms["control"]),
                            "B": (with_result, arms["treatment"]),
                        }
                        a_is_with = False
                    judge_arms = [arms["judge-1"], arms["judge-2"]]
                    judge_envs = [
                        arm_envs["judge-1"],
                        arm_envs["judge-2"],
                    ]
                    stage_judge_evidence(result_dir, judge_arms, sides)
                    verdict, judge_result, judge_arm = grade(
                        case["prompt"],
                        output_assertions,
                        process_assertions,
                        judge_arms,
                        judge_envs,
                    )
                    calls += 1
                    (result_dir / "judge.txt").write_text(judge_result.output)
                    write_run_evidence(
                        result_dir / "judge-evidence",
                        judge_result,
                        judge_arm,
                    )

                    if a_is_with:
                        a_output = verdict["a_output"]
                        a_process = verdict["a_process"]
                        b_output = verdict["b_output"]
                        b_process = verdict["b_process"]
                    else:
                        a_output = verdict["b_output"]
                        a_process = verdict["b_process"]
                        b_output = verdict["a_output"]
                        b_process = verdict["a_process"]
                    total_assertions = len(output_assertions) + len(process_assertions)
                    rep_results.append(
                        {
                            "output_assertions": len(output_assertions),
                            "process_assertions": len(process_assertions),
                            "with_output": a_output,
                            "with_process": a_process,
                            "without_output": b_output,
                            "without_process": b_process,
                            "with_pass": a_output + a_process == total_assertions,
                            "without_pass": b_output + b_process == total_assertions,
                        }
                    )
                    if repo_snapshot() != clean_tree:
                        raise RuntimeError(
                            "SANDBOX BREACH: repo tree changed during rep; inspect git status"
                        )
                    print(
                        f"OK   {key} rep{rep}: "
                        f"with={a_output + a_process}/{total_assertions} "
                        f"without={b_output + b_process}/{total_assertions}"
                    )
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{key} rep{rep}: {exc}")
                    print(f"FAIL {key} rep{rep}: {exc}")

            if rep_results:
                results[key] = aggregate_reps(rep_results)

    write_fingerprint_manifest(
        iteration / "fingerprints.json", "compliance", fingerprint_records
    )
    (iteration / "meta.json").write_text(
        json.dumps(
            {
                "date": datetime.now(timezone.utc).isoformat(),
                "provider": PROVIDER,
                "model": MODEL,
                "judge_provider": JUDGE_PROVIDER,
                "judge_model": JUDGE_MODEL,
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
    (iteration / "benchmark.json").write_text(json.dumps(results, indent=2) + "\n")
    (iteration / "errors.json").write_text(json.dumps(errors, indent=2) + "\n")

    print(f"\n{len(results)} evals, {calls} calls, {len(errors)} errors")
    for key, result in results.items():
        print(
            f"  {key}: tasks with {result['with_task_passes']}/{result['max_task_passes']}, "
            f"without {result['without_task_passes']}/{result['max_task_passes']}; "
            f"assertion points {result['with_assertion_points']}/{result['max_assertion_points']} "
            f"vs {result['without_assertion_points']}/{result['max_assertion_points']}"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
