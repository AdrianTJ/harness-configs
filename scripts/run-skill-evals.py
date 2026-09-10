#!/usr/bin/env python3
"""Pilot skill evals on Muse Spark through pi. Run: scripts/run-skill-evals.py.

Differential design (best practice for skill evals):
  - WITHOUT arm: sterile profile + --no-skills. The ONLY difference in the
    WITH arm is `--skill <dir>` for the skill under test.
  - A/B sides are swapped on even reps to cancel judge position bias.
  - Judge grades each assertion against each side with quoted evidence and
    ends with machine-readable A-PASS / B-PASS lines; unparseable verdicts
    retry once, then record an error.
  - One rep proves nothing on a stochastic system: budget allows ~6 reps for
    single-eval skills, ~3 for two-eval skills (20 calls each).

Cost: 3 calls per eval per rep (2 target + 1 judge).
NEVER in CI. Writes gitignored eval-runs/iteration-N/; prints the rollup.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROVIDER = os.environ.get("EVAL_PROVIDER", "opencode-go")
MODEL = os.environ.get("EVAL_MODEL", "muse-spark-1.3-contributor")
CALL_TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "300"))
# Pilot budget: 20 calls each -> deslop 6 reps, write-skill 3 reps.
PILOT = {"deslop": 6, "write-skill": 3}

JUDGE_TEMPLATE = """You are grading two anonymous responses to the same user request.
For EACH numbered assertion and EACH response, write PASS or FAIL followed by a
short quote from that response as evidence. Judge only what is written: a
response that never addresses an assertion FAILs it.

User request:
{prompt}

Assertions:
{assertions}

Response A:
{out_a}

Response B:
{out_b}

End with exactly these two lines and nothing after them:
A-PASS: <number of assertions Response A passed>
B-PASS: <number of assertions Response B passed>
"""


def run_pi(args, cwd, prof_env):
    """Run pi -p once under the sterile eval profile; return stdout or raise."""
    try:
        p = subprocess.run(
            ["pi", "-p", "--no-session", "--provider", PROVIDER, "--model", MODEL, *args],
            capture_output=True, text=True, timeout=CALL_TIMEOUT, cwd=cwd, env=prof_env,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"pi call timed out after {CALL_TIMEOUT}s")
    if p.returncode != 0:
        raise RuntimeError(f"pi exited {p.returncode}: {p.stderr.strip()[-500:]}")
    return p.stdout.strip()


def parse_verdict(text):
    """Extract (a_pass, b_pass) or return None."""
    a = re.search(r"^A-PASS:\s*(\d+)", text, re.M)
    b = re.search(r"^B-PASS:\s*(\d+)", text, re.M)
    if not a or not b:
        return None
    return int(a.group(1)), int(b.group(1))


def grade(prompt, assertions, out_a, out_b, workdir, prof_env):
    """Judge both sides; retry once on unparseable verdict."""
    numbered = "\n".join(f"{i + 1}. {a}" for i, a in enumerate(assertions))
    judge_prompt = JUDGE_TEMPLATE.format(
        prompt=prompt, assertions=numbered, out_a=out_a, out_b=out_b)
    last = ""
    for _ in range(2):
        last = run_pi([judge_prompt], workdir, prof_env)
        verdict = parse_verdict(last)
        if verdict is not None:
            return verdict, last
    raise RuntimeError(f"judge verdict unparseable after retry; output tail: {last[-300:]}")


def load_evals(skill):
    spec = json.loads((REPO / "shared" / "skills" / skill / "evals" / "evals.json").read_text())
    assert spec["skill_name"] == skill, f"skill_name mismatch in {skill}"
    return spec["evals"]


def main():
    pairs = sys.argv[1:] or [f"{s}={r}" for s, r in PILOT.items()]
    plan = []
    for pair in pairs:
        skill, _, reps = pair.partition("=")
        plan.append((skill, int(reps or PILOT.get(skill, 1))))

    # Sterile profile: auth symlinked from the real base, never copied.
    trit = tempfile.mkdtemp(prefix="skill-evals-")
    env = dict(os.environ, PI_PROFILES_ROOT=str(Path(trit) / "profiles"),
               PI_PROFILE_BASE_DIR=str(Path.home() / ".pi" / "agent"))
    subprocess.run(["pi-profile", "create", "eval"], check=True, capture_output=True,
                   env=env)
    prof_env = dict(os.environ, PI_CODING_AGENT_DIR=str(Path(trit) / "profiles" / "eval"))
    workdir = Path(trit) / "work"
    workdir.mkdir()

    # Isolate skill discovery: the profile dir may gain skills later; --no-skills
    # keeps both arms clean and the WITH arm adds exactly one skill.
    it = REPO / "eval-runs" / "iteration-1"
    results, errors, calls = {}, [], 0
    for skill, reps in plan:
        skill_dir = REPO / "shared" / "skills" / skill
        for ev in load_evals(skill):
            key = f"{skill}/{ev['id']}"
            rep_results = []
            for rep in range(1, reps + 1):
                d = it / skill / ev["id"] / f"rep{rep}"
                d.mkdir(parents=True, exist_ok=True)
                try:
                    with_out = run_pi(["--no-skills", "--skill", str(skill_dir), ev["prompt"]],
                                      workdir, prof_env)
                    calls += 1
                    without_out = run_pi(["--no-skills", ev["prompt"]], workdir, prof_env)
                    calls += 1
                    (d / "with.txt").write_text(with_out)
                    (d / "without.txt").write_text(without_out)
                    # Swap sides on even reps: position bias cancels out.
                    if rep % 2 == 1:
                        a_out, b_out, a_is_with = with_out, without_out, True
                    else:
                        a_out, b_out, a_is_with = without_out, with_out, False
                    (a, b), judge_out = grade(ev["prompt"], ev["assertions"], a_out, b_out,
                                             workdir, prof_env)
                    calls += 1
                    (d / "judge.txt").write_text(judge_out)
                    with_pass, without_pass = (a, b) if a_is_with else (b, a)
                    rep_results.append({"with": with_pass, "without": without_pass,
                                        "n": len(ev["assertions"])})
                    print(f"OK   {key} rep{rep}: with={with_pass} without={without_pass}")
                except Exception as exc:  # noqa: BLE001 — one flake must not kill the sweep
                    errors.append(f"{key} rep{rep}: {exc}")
                    print(f"FAIL {key} rep{rep}: {exc}")
            if rep_results:
                n = rep_results[0]["n"]
                w = sum(r["with"] for r in rep_results)
                wo = sum(r["without"] for r in rep_results)
                results[key] = {"reps": len(rep_results), "assertions": n,
                                "with_total": w, "without_total": wo,
                                "lift": w - wo, "max": len(rep_results) * n}

    (it / "meta.json").write_text(json.dumps({
        "date": datetime.now(timezone.utc).isoformat(), "provider": PROVIDER,
        "model": MODEL, "plan": plan, "calls": calls,
        "repo": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                               text=True, cwd=REPO).stdout.strip(),
    }, indent=2))
    (it / "benchmark.json").write_text(json.dumps(results, indent=2))

    print(f"\n{len(results)} evals, {calls} calls, {len(errors)} errors")
    for key, r in results.items():
        print(f"  {key}: with {r['with_total']}/{r['max']}  "
              f"without {r['without_total']}/{r['max']}  lift {r['lift']:+d}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
