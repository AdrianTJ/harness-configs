#!/usr/bin/env python3
"""Trigger probes: does the skill fire on realistic prompts? Run: scripts/run-trigger-probes.py [skill=reps ...].

Unlike run-skill-evals.py (which force-loads via --skill and measures
COMPLIANCE), this measures ROUTING: the probe profile has every skill linked
exactly like a real install, prompts never name any skill, and a hit is
detected by skill-distinctive fingerprints in the output.

Each probe also runs an unlinked CONTROL (target skill's symlink removed):
if the control hits too, the fingerprints are contaminated (background
knowledge, AGENTS.md) — not evidence of triggering. Report trigger_rate
alongside control_rate; the difference is the signal.

Cost: 2 calls per probe per rep (linked + control). NEVER in CI.
Writes gitignored eval-runs/iteration-N/triggers/.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROVIDER = os.environ.get("EVAL_PROVIDER", "opencode-go")
MODEL = os.environ.get("EVAL_MODEL", "muse-spark-1.3-contributor")
CALL_TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "300"))
DEFAULT_REPS = 5


def run_pi(args, cwd, env):
    try:
        p = subprocess.run(
            ["pi", "-p", "--no-session", "--provider", PROVIDER, "--model", MODEL, *args],
            capture_output=True, text=True, timeout=CALL_TIMEOUT, cwd=cwd, env=env,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"pi call timed out after {CALL_TIMEOUT}s")
    if p.returncode != 0:
        raise RuntimeError(f"pi exited {p.returncode}: {p.stderr.strip()[-500:]}")
    return p.stdout.strip()


def repo_snapshot():
    p = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                       text=True, cwd=REPO)
    return p.stdout


def hit(output, fingerprints):
    low = output.lower()
    return [f for f in fingerprints if f.lower() in low]


def main():
    pairs = sys.argv[1:]
    plan = []
    if pairs:
        for pair in pairs:
            skill, _, reps = pair.partition("=")
            plan.append((skill, int(reps or DEFAULT_REPS)))
    else:
        for d in sorted((REPO / "shared" / "skills").iterdir()):
            spec_file = d / "evals" / "evals.json"
            if not spec_file.exists():
                continue
            spec = json.loads(spec_file.read_text())
            if spec.get("trigger_probes"):
                plan.append((d.name, DEFAULT_REPS))
    if not plan:
        print("no skills with trigger_probes; nothing to do")
        return 0

    trit = tempfile.mkdtemp(prefix="trigger-probes-")
    # Clean-room HOME: the live ~ exposes the repo (via linked dotfiles) and
    # every installed skill. A tool-using run can read skill files straight
    # off disk, which voids trigger measurement. Under fakehome the only
    # visible skills are the profile's own symlinks.
    fakehome = str(Path(trit) / "fakehome")
    Path(fakehome).mkdir()
    env = dict(os.environ, PI_PROFILES_ROOT=str(Path(trit) / "profiles"),
               PI_PROFILE_BASE_DIR=str(Path.home() / ".pi" / "agent"),
               HOME=fakehome)
    subprocess.run(["pi-profile", "create", "probe"], check=True, capture_output=True, env=env)
    prof_dir = Path(trit) / "profiles" / "probe"
    prof_env = dict(os.environ, PI_CODING_AGENT_DIR=str(prof_dir), HOME=fakehome)
    workdir = Path(trit) / "work"
    workdir.mkdir()
    # Mirror a real install: every shared skill symlinked into the profile.
    for d in sorted((REPO / "shared" / "skills").iterdir()):
        if (d / "SKILL.md").exists():
            (prof_dir / "skills").mkdir(exist_ok=True)
            link = prof_dir / "skills" / d.name
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to(d.resolve())

    it = REPO / "eval-runs" / "iteration-1" / "triggers"
    results, errors, calls = {}, [], 0
    clean_tree = repo_snapshot()
    for skill, reps in plan:
        spec = json.loads((REPO / "shared" / "skills" / skill / "evals" / "evals.json").read_text())
        for tp in spec.get("trigger_probes", []):
            key = f"{skill}/{tp['id']}"
            hits, chits = 0, 0
            for rep in range(1, reps + 1):
                d = it / skill / tp["id"] / f"rep{rep}"
                d.mkdir(parents=True, exist_ok=True)
                try:
                    out = run_pi([tp["prompt"]], workdir, prof_env)
                    calls += 1
                    (d / "linked.txt").write_text(out)
                    link = prof_dir / "skills" / skill
                    # Control: target skill unlinked for this rep only.
                    assert link.is_symlink(), f"{skill} not symlinked in probe profile"
                    tmp = link.with_suffix(".off")
                    link.rename(tmp)
                    try:
                        cout = run_pi([tp["prompt"]], workdir, prof_env)
                    finally:
                        tmp.rename(link)
                    calls += 1
                    (d / "control.txt").write_text(cout)
                    h, ch = hit(out, tp["fingerprints"]), hit(cout, tp["fingerprints"])
                    hits += bool(h)
                    chits += bool(ch)
                    if repo_snapshot() != clean_tree:
                        raise RuntimeError("SANDBOX BREACH during trigger probe rep")
                    print(f"OK   {key} rep{rep}: linked={'Y' if h else '-'} "
                          f"control={'Y' if ch else '-'}")
                except Exception as exc:  # noqa: BLE001 — one flake must not kill the run
                    errors.append(f"{key} rep{rep}: {exc}")
                    print(f"FAIL {key} rep{rep}: {exc}")
            results[key] = {"reps": reps, "trigger_rate": hits / reps,
                            "control_rate": chits / reps,
                            "lift": (hits - chits) / reps}

    (it / "meta.json").write_text(json.dumps({
        "date": datetime.now(timezone.utc).isoformat(), "provider": PROVIDER,
        "model": MODEL, "plan": plan, "calls": calls,
        "repo": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                               text=True, cwd=REPO).stdout.strip(),
    }, indent=2))
    (it / "triggers.json").write_text(json.dumps(results, indent=2))
    print(f"\n{len(results)} probes, {calls} calls, {len(errors)} errors")
    for key, r in results.items():
        print(f"  {key}: trigger {r['trigger_rate']:.0%}  "
              f"control {r['control_rate']:.0%}  lift {r['lift']:+.0%}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
