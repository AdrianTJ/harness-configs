#!/usr/bin/env python3
"""Judge-verdict parsing and binary/assertion scoring for skill evals."""

import re
from typing import Mapping, Sequence


_VERDICT_FIELDS = {
    "a_output": "A-OUTPUT",
    "a_process": "A-PROCESS",
    "b_output": "B-OUTPUT",
    "b_process": "B-PROCESS",
    "a_total": "A-PASS",
    "b_total": "B-PASS",
}


def _parse_counts(text: str) -> dict[str, int]:
    counts = {}
    for field, label in _VERDICT_FIELDS.items():
        match = re.search(rf"^{label}:\s*(\d+)$", text, re.M)
        if not match:
            raise ValueError(f"judge verdict missing {label}")
        counts[field] = int(match.group(1))
    return counts


def parse_judge_verdict(
    text: str,
    output_assertions: int,
    process_assertions: int,
) -> dict[str, int]:
    counts = _parse_counts(text)
    limits = {
        "output": output_assertions,
        "process": process_assertions,
        "total": output_assertions + process_assertions,
    }
    for side in ("a", "b"):
        for kind in ("output", "process", "total"):
            value = counts[f"{side}_{kind}"]
            if not 0 <= value <= limits[kind]:
                raise ValueError(
                    f"{side.upper()}-{kind.upper()} score {value} is outside "
                    f"0..{limits[kind]}"
                )
        if counts[f"{side}_total"] != counts[f"{side}_output"] + counts[f"{side}_process"]:
            raise ValueError(f"{side.upper()}-PASS does not equal its component scores")
    return counts


def trigger_metrics(
    *,
    reps: int,
    expect_activation: bool,
    fingerprint_hits: int,
    control_fingerprint_hits: int,
    skill_reads: int,
    control_skill_reads: int,
) -> dict:
    if reps <= 0:
        raise ValueError("trigger probe reps must be positive")
    trigger_rate = fingerprint_hits / reps
    control_rate = control_fingerprint_hits / reps
    activation_rate = skill_reads / reps
    control_activation_rate = control_skill_reads / reps
    return {
        "reps": reps,
        "expect_activation": expect_activation,
        "trigger_rate": trigger_rate,
        "control_rate": control_rate,
        "lift": trigger_rate - control_rate,
        "linked_skill_read_rate": activation_rate,
        "control_skill_read_rate": control_activation_rate,
        "skill_miss_rate": 1 - activation_rate if expect_activation else 0.0,
        "false_positive_rate": activation_rate if not expect_activation else 0.0,
        "fingerprint_miss_rate": 1 - trigger_rate if expect_activation else 0.0,
        "fingerprint_false_positive_rate": (
            trigger_rate if not expect_activation else 0.0
        ),
    }


def aggregate_reps(reps: Sequence[Mapping]) -> dict:
    if not reps:
        raise ValueError("cannot aggregate zero eval repetitions")
    first = reps[0]
    output_assertions = int(first["output_assertions"])
    process_assertions = int(first["process_assertions"])
    for rep in reps:
        if (
            rep["output_assertions"] != output_assertions
            or rep["process_assertions"] != process_assertions
        ):
            raise ValueError("eval assertion counts changed across repetitions")

    count = len(reps)
    with_task_passes = sum(bool(rep["with_pass"]) for rep in reps)
    without_task_passes = sum(bool(rep["without_pass"]) for rep in reps)
    with_assertion_points = sum(
        int(rep["with_output"]) + int(rep["with_process"]) for rep in reps
    )
    without_assertion_points = sum(
        int(rep["without_output"]) + int(rep["without_process"]) for rep in reps
    )
    max_points = count * (output_assertions + process_assertions)
    return {
        "reps": count,
        "assertions": output_assertions + process_assertions,
        "output_assertions": output_assertions,
        "process_assertions": process_assertions,
        "with_task_passes": with_task_passes,
        "without_task_passes": without_task_passes,
        "max_task_passes": count,
        "with_task_pass_rate": with_task_passes / count,
        "without_task_pass_rate": without_task_passes / count,
        "task_pass_lift": (with_task_passes - without_task_passes) / count,
        "with_assertion_points": with_assertion_points,
        "without_assertion_points": without_assertion_points,
        "max_assertion_points": max_points,
        # Backward-compatible names now mean assertion points, not task passes.
        "with_total": with_assertion_points,
        "without_total": without_assertion_points,
        "max": max_points,
        "lift": with_assertion_points - without_assertion_points,
    }
