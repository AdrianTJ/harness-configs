#!/usr/bin/env python3
"""Tests for parsing Pi JSON event streams in the eval runner."""

import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pi_eval_client import parse_pi_events, require_success, run_setup


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


if __name__ == "__main__":
    unittest.main()
