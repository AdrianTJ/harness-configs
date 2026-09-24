#!/usr/bin/env python3
"""Regression tests for skill-eval treatment/control isolation.

These tests replace pi and pi-profile with deterministic fakes. The fake pi
writes a sentinel in the treatment workspace; the control must not see it.
No model API is called.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
EVAL_RUNS = ROOT / "eval-runs"

FAKE_PI = r'''#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path

args = sys.argv[1:]
if "--version" in args:
    print("test-pi 1.0")
    raise SystemExit(0)

def option(name, default=""):
    try:
        return args[args.index(name) + 1]
    except (ValueError, IndexError):
        return default

def emit(provider, model, text, tools=()):
    cwd = Path.cwd()
    events = [
        {"type": "session", "version": 3, "id": "fake-session", "timestamp": "2026-01-01T00:00:00Z", "cwd": str(cwd)},
        {"type": "agent_start"},
    ]
    for index, (name, tool_args) in enumerate(tools, 1):
        call_id = f"call-{index}"
        events.append({"type": "tool_execution_start", "toolCallId": call_id, "toolName": name, "args": tool_args})
        events.append({"type": "tool_execution_end", "toolCallId": call_id, "result": "ok", "isError": False})
    message = {
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "api": "fake",
        "provider": provider,
        "model": model,
        "usage": {
            "input": 10, "output": 5, "cacheRead": 0, "cacheWrite": 0,
            "reasoning": 0, "totalTokens": 15,
            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0, "total": 0},
        },
        "stopReason": "stop",
    }
    events.append({"type": "message_end", "message": message})
    events.append({"type": "agent_end", "messages": [message], "willRetry": False})
    for event in events:
        print(json.dumps(event, separators=(",", ":")))

provider = option("--provider", "fake-provider")
model = option("--model", "fake-model")
judge_prompt = next((arg for arg in args if "OUTPUT ASSERTIONS:" in arg), "")
if judge_prompt:
    for side in ("A", "B"):
        for name in ("environment.json", "events.jsonl", "transcript.json"):
            if not (Path.cwd() / side / name).is_file():
                raise SystemExit(f"judge evidence missing: {side}/{name}")
    output_count = int(re.search(r"OUTPUT ASSERTIONS: (\d+)", judge_prompt).group(1))
    process_count = int(re.search(r"PROCESS ASSERTIONS: (\d+)", judge_prompt).group(1))
    total = output_count + process_count
    text = "\n".join([
        f"A-OUTPUT: {output_count}", f"A-PROCESS: {process_count}", f"A-PASS: {total}",
        f"B-OUTPUT: {output_count}", f"B-PROCESS: {process_count}", f"B-PASS: {total}",
    ])
    emit(provider, model, text)
    raise SystemExit(0)

cwd = Path.cwd()
home = Path(os.environ["HOME"])
profile = Path(os.environ["PI_CODING_AGENT_DIR"])
sentinels = (
    cwd / "arm-sentinel.txt",
    home / "arm-sentinel.txt",
    profile / "arm-sentinel.txt",
)

if "--no-skills" in args:
    if "--skill" in args:
        for sentinel in sentinels:
            sentinel.write_text("treatment wrote this\n")
        emit(provider, model, "TREATMENT_CLEAN", [("write", {"path": "arm-sentinel.txt"})])
    else:
        leaked = any(sentinel.exists() for sentinel in sentinels)
        emit(provider, model, "CONTROL_LEAK" if leaked else "CONTROL_CLEAN")
    raise SystemExit(0)

if (profile / "skills" / "log-decision" / "SKILL.md").exists():
    for sentinel in sentinels:
        sentinel.write_text("linked arm wrote this\n")
    emit(provider, model, "DEC-001", [("read", {"path": "skills/log-decision/SKILL.md"})])
else:
    leaked = any(sentinel.exists() for sentinel in sentinels)
    emit(provider, model, "CONTROL_LEAK" if leaked else "CONTROL_CLEAN")
'''

FAKE_PI_PROFILE = r'''#!/usr/bin/env python3
import os
import sys
from pathlib import Path

if len(sys.argv) < 3 or sys.argv[1] != "create":
    raise SystemExit(2)
profile = Path(os.environ["PI_PROFILES_ROOT"]) / sys.argv[2]
(profile / "skills").mkdir(parents=True, exist_ok=True)
print(profile)
'''


class EvalIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.bin_dir = Path(self.tempdir.name) / "bin"
        self.bin_dir.mkdir()
        self._write_executable(self.bin_dir / "pi", FAKE_PI)
        self._write_executable(self.bin_dir / "pi-profile", FAKE_PI_PROFILE)
        self.iteration = f"test-isolation-{os.getpid()}-{self._testMethodName}"
        self.eval_dir = EVAL_RUNS / self.iteration

    def tearDown(self):
        shutil.rmtree(self.eval_dir, ignore_errors=True)
        self.tempdir.cleanup()

    @staticmethod
    def _write_executable(path: Path, content: str):
        path.write_text(content)
        path.chmod(0o755)

    def _run(self, script: str, *args: str):
        env = self._env()
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

    def _status(self, run_dir: Path, *args: str):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "eval-status.py"),
                str(run_dir),
                "--check",
                *args,
            ],
            cwd=ROOT,
            env=self._env(),
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

    def _env(self):
        env = os.environ.copy()
        env["PATH"] = f"{self.bin_dir}{os.pathsep}{env.get('PATH', '')}"
        env["EVAL_PROVIDER"] = "test-provider"
        env["EVAL_MODEL"] = "test-model"
        env["EVAL_JUDGE_PROVIDER"] = "test-judge-provider"
        env["EVAL_JUDGE_MODEL"] = "test-judge-model"
        env["EVAL_TIMEOUT"] = "10"
        env["EVAL_ITERATION"] = self.iteration
        return env

    def test_compliance_control_cannot_see_treatment_workspace(self):
        result = self._run("run-skill-evals.py", "harness-configs=1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        treatment = (
            self.eval_dir
            / "harness-configs"
            / "dry-run-before-link"
            / "rep1"
            / "with.txt"
        ).read_text()
        control = (
            self.eval_dir
            / "harness-configs"
            / "dry-run-before-link"
            / "rep1"
            / "without.txt"
        ).read_text()
        self.assertIn("TREATMENT_CLEAN", treatment)
        self.assertIn("CONTROL_CLEAN", control)
        self.assertNotIn("CONTROL_LEAK", control)

        result_dir = self.eval_dir / "harness-configs" / "dry-run-before-link" / "rep1"
        for evidence_dir in ("A-evidence", "B-evidence", "judge-evidence"):
            for name in ("events.jsonl", "transcript.json", "environment.json"):
                self.assertTrue((result_dir / evidence_dir / name).is_file())

        benchmark = json.loads((self.eval_dir / "benchmark.json").read_text())
        score = benchmark["harness-configs/dry-run-before-link"]
        self.assertEqual(score["with_task_passes"], 1)
        self.assertEqual(score["without_task_passes"], 1)
        self.assertEqual(score["with_assertion_points"], 5)

        fingerprints = self.eval_dir / "fingerprints.json"
        self.assertTrue(fingerprints.is_file())
        manifest = json.loads(fingerprints.read_text())
        record = manifest["records"]["harness-configs/dry-run-before-link"]
        self.assertEqual(record["config"]["judge_model"], "test-judge-model")
        self.assertNotEqual(record["config"]["model"], record["config"]["judge_model"])
        status = self._status(self.eval_dir)
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)

    def test_trigger_control_cannot_see_linked_workspace(self):
        result = self._run("run-trigger-probes.py", "log-decision=1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        linked = (
            self.eval_dir
            / "triggers"
            / "log-decision"
            / "fires-on-killed-migration"
            / "rep1"
            / "linked.txt"
        ).read_text()
        control = (
            self.eval_dir
            / "triggers"
            / "log-decision"
            / "fires-on-killed-migration"
            / "rep1"
            / "control.txt"
        ).read_text()
        self.assertIn("DEC-001", linked)
        self.assertIn("CONTROL_CLEAN", control)
        self.assertNotIn("CONTROL_LEAK", control)

        result_dir = (
            self.eval_dir
            / "triggers"
            / "log-decision"
            / "fires-on-killed-migration"
            / "rep1"
        )
        for evidence_dir in ("linked-evidence", "control-evidence"):
            for name in ("events.jsonl", "transcript.json", "environment.json"):
                self.assertTrue((result_dir / evidence_dir / name).is_file())
        triggers = json.loads(
            (self.eval_dir / "triggers" / "triggers.json").read_text()
        )
        self.assertEqual(
            triggers["log-decision/fires-on-killed-migration"]["linked_skill_read_rate"],
            1.0,
        )

        fingerprints = self.eval_dir / "triggers" / "fingerprints.json"
        self.assertTrue(fingerprints.is_file())
        status = self._status(self.eval_dir / "triggers")
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)

    def test_fingerprint_status_rejects_changed_result(self):
        result = self._run("run-skill-evals.py", "harness-configs=1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        path = self.eval_dir / "fingerprints.json"
        manifest = json.loads(path.read_text())
        key = "harness-configs/dry-run-before-link"
        manifest["records"][key]["fingerprints"]["combined"] = "0" * 64
        path.write_text(json.dumps(manifest, indent=2) + "\n")

        status = self._status(self.eval_dir)
        self.assertNotEqual(status.returncode, 0)
        self.assertIn("STALE", status.stdout + status.stderr)

    def test_status_check_fails_on_recorded_run_errors(self):
        result = self._run("run-skill-evals.py", "harness-configs=1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        (self.eval_dir / "errors.json").write_text(
            json.dumps(["rep1: pi run failed: provider 400"]) + "\n"
        )
        status = self._status(self.eval_dir)
        self.assertNotEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertIn("ERROR", status.stdout)
        self.assertIn("provider 400", status.stdout)

    def test_status_check_fails_when_case_has_no_result(self):
        result = self._run("run-skill-evals.py", "harness-configs=1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        benchmark_path = self.eval_dir / "benchmark.json"
        benchmark = json.loads(benchmark_path.read_text())
        benchmark.pop("harness-configs/dry-run-before-link")
        benchmark_path.write_text(json.dumps(benchmark) + "\n")

        status = self._status(self.eval_dir)
        self.assertNotEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertIn("NORESULT", status.stdout)

    def test_status_check_fails_when_results_file_is_missing(self):
        result = self._run("run-skill-evals.py", "harness-configs=1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        (self.eval_dir / "benchmark.json").unlink()
        status = self._status(self.eval_dir)
        self.assertNotEqual(status.returncode, 0, status.stdout + status.stderr)
        self.assertIn("NORESULT", status.stdout)


if __name__ == "__main__":
    unittest.main()
