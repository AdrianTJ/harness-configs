#!/usr/bin/env python3
"""Tests for parsing Pi JSON event streams in the eval runner."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pi_eval_client
from pi_eval_client import parse_pi_events, require_success, run_pi, run_setup


class PiEventParserTests(unittest.TestCase):
    def test_extracts_output_runtime_usage_and_tool_evidence(self):
        raw = "\n".join(
            [
                '{"type":"session","version":3,"id":"abc","cwd":"/tmp/run"}',
                '{"type":"agent_start"}',
                '{"type":"tool_execution_start","toolCallId":"t1","toolName":"read","args":{"path":"README.md"}}',
                '{"type":"tool_execution_end","toolCallId":"t1","result":"contents","isError":false}',
                '{"type":"tool_execution_start","toolCallId":"t2","toolName":"bash","args":{"command":"pytest -q"}}',
                '{"type":"tool_execution_end","toolCallId":"t2","result":"ok","isError":false}',
                '{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"Done."}],"provider":"test-provider","model":"test-model","usage":{"input":10,"output":3,"cacheRead":2,"cacheWrite":1,"totalTokens":16,"cost":{"input":0,"output":0,"cacheRead":0,"cacheWrite":0,"total":0}},"stopReason":"stop"}}',
                '{"type":"agent_end","messages":[],"willRetry":false}',
            ]
        )

        result = parse_pi_events(raw)

        self.assertEqual(result.output, "Done.")
        self.assertEqual(result.provider, "test-provider")
        self.assertEqual(result.model, "test-model")
        self.assertEqual(result.usage["input"], 10)
        self.assertEqual(result.usage["output"], 3)
        self.assertEqual(result.usage["totalTokens"], 16)
        self.assertEqual(result.tool_calls[0]["name"], "read")
        self.assertEqual(result.files_read, ["README.md"])
        self.assertEqual(result.commands, ["pytest -q"])
        self.assertEqual(result.errors, [])

    def test_collects_errors_and_modifies_from_tool_names(self):
        raw = "\n".join(
            [
                '{"type":"tool_execution_start","toolCallId":"t1","toolName":"edit","args":{"path":"src/app.py"}}',
                '{"type":"tool_execution_end","toolCallId":"t1","result":null,"isError":true}',
                '{"type":"message_end","message":{"role":"assistant","content":[],"provider":"p","model":"m","usage":{"input":1,"output":0,"cacheRead":0,"cacheWrite":0,"totalTokens":1,"cost":{"input":0,"output":0,"cacheRead":0,"cacheWrite":0,"total":0}},"stopReason":"error","errorMessage":"boom"}}',
                '{"type":"agent_end","messages":[],"willRetry":false}',
            ]
        )

        result = parse_pi_events(raw)

        self.assertEqual(result.files_modified, ["src/app.py"])
        self.assertTrue(any("boom" in error for error in result.errors))
        self.assertIn("boom", result.fatal_error)
        self.assertTrue(result.tool_calls[0]["isError"])
        with self.assertRaises(RuntimeError):
            require_success(result)

    def test_rejects_non_json_stdout(self):
        with self.assertRaises(RuntimeError):
            parse_pi_events("not-json\n")

    def test_setup_runs_identical_fixture_commands_in_each_arm(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            for name in ("treatment", "control"):
                arm = root / name
                arm.mkdir()
                run_setup(
                    ["printf 'fixture\\n' > input.txt"],
                    arm,
                    dict(os.environ),
                    timeout=10,
                )
            self.assertEqual(
                (root / "treatment" / "input.txt").read_text(),
                "fixture\n",
            )
            self.assertEqual(
                (root / "control" / "input.txt").read_text(),
                "fixture\n",
            )


GOOD_EVENT = json.dumps(
    {
        "type": "message_end",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": "Done."}],
            "provider": "p",
            "model": "m",
            "usage": {"input": 1, "output": 1, "totalTokens": 2},
            "stopReason": "stop",
        },
    }
)


class RunPiRetryTests(unittest.TestCase):
    """Transient upstream failures retry; real failures still raise."""

    def setUp(self):
        self.sleeps = []
        patcher = mock.patch.object(pi_eval_client.time, "sleep", self.sleeps.append)
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def _completed(returncode=0, stdout="", stderr=""):
        return mock.Mock(returncode=returncode, stdout=stdout, stderr=stderr)

    def _run(self, outcomes, args=None):
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            return outcomes[len(calls) - 1]

        with mock.patch.object(pi_eval_client.subprocess, "run", fake_run):
            result = run_pi(
                "test-provider",
                "test-model",
                args or ["prompt"],
                Path("."),
                dict(os.environ),
                timeout=10,
            )
        return result, calls

    def test_transient_provider_400_is_retried_then_succeeds(self):
        upstream_400 = self._completed(
            returncode=1,
            stderr='400: {"message":"Upstream request failed: reasoning_effort is not allowed"}',
        )
        result, calls = self._run([upstream_400, self._completed(stdout=GOOD_EVENT)])
        self.assertEqual(len(calls), 2)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.output, "Done.")
        self.assertEqual(len(self.sleeps), 1)

    def test_fatal_error_in_stream_is_retried_when_transient(self):
        fatal_503 = self._completed(
            stdout=json.dumps(
                {
                    "type": "message_end",
                    "message": {
                        "role": "assistant",
                        "content": [],
                        "usage": {},
                        "stopReason": "error",
                        "errorMessage": "503: upstream overloaded",
                    },
                }
            )
        )
        result, calls = self._run([fatal_503, self._completed(stdout=GOOD_EVENT)])
        self.assertEqual(len(calls), 2)
        self.assertEqual(result.attempts, 2)

    def test_timeout_is_not_retried(self):
        def fake_run(command, **kwargs):
            raise pi_eval_client.subprocess.TimeoutExpired(command, 10)

        with mock.patch.object(pi_eval_client.subprocess, "run", fake_run):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                run_pi("p", "m", ["prompt"], Path("."), dict(os.environ), timeout=10)
        self.assertEqual(self.sleeps, [])

    def test_persistent_transient_failure_raises_after_max_attempts(self):
        upstream_400 = self._completed(
            returncode=1,
            stderr="400: Upstream request failed: not allowed",
        )
        with self.assertRaisesRegex(RuntimeError, "pi exited 1"):
            self._run([upstream_400] * 3)
        self.assertEqual(len(self.sleeps), pi_eval_client.RETRY_ATTEMPTS - 1)

    def test_non_transient_exit_is_not_retried(self):
        broken = self._completed(returncode=2, stderr="unknown flag --bogus")
        with self.assertRaisesRegex(RuntimeError, "pi exited 2"):
            self._run([broken])
        self.assertEqual(self.sleeps, [])


if __name__ == "__main__":
    unittest.main()
