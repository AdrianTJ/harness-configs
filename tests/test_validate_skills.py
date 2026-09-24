#!/usr/bin/env python3
"""Focused tests for skill eval-spec validation."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_skills", ROOT / "scripts" / "validate-skills.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EvalSpecValidationTests(unittest.TestCase):
    def write_spec(self, eval_case):
        self.tempdir = tempfile.TemporaryDirectory()
        skill = Path(self.tempdir.name) / "sample"
        evals = skill / "evals"
        evals.mkdir(parents=True)
        (skill / "SKILL.md").write_text("# Sample\n")
        path = evals / "evals.json"
        path.write_text(
            json.dumps({"skill_name": "sample", "evals": [eval_case]})
        )
        return path

    def tearDown(self):
        tempdir = getattr(self, "tempdir", None)
        if tempdir is not None:
            tempdir.cleanup()

    def test_accepts_optional_transcript_assertions(self):
        path = self.write_spec(
            {
                "id": "case",
                "prompt": "Do the thing",
                "assertions": ["Output is correct"],
                "transcript_assertions": ["The agent ran the verification command"],
            }
        )
        self.assertEqual(MODULE.check_evals(path), [])

    def test_rejects_malformed_transcript_assertions(self):
        path = self.write_spec(
            {
                "id": "case",
                "prompt": "Do the thing",
                "assertions": ["Output is correct"],
                "transcript_assertions": "ran a command",
            }
        )
        self.assertTrue(
            any("transcript_assertions" in error for error in MODULE.check_evals(path))
        )

    def test_accepts_fixture_object_with_explicit_destination(self):
        self.tempdir = tempfile.TemporaryDirectory()
        skill = Path(self.tempdir.name) / "sample"
        source = skill / "evals" / "files" / "project" / "config.txt"
        source.parent.mkdir(parents=True)
        source.write_text("fixture")
        (skill / "SKILL.md").write_text("# Sample\n")
        path = skill / "evals" / "evals.json"
        path.write_text(
            json.dumps(
                {
                    "skill_name": "sample",
                    "evals": [
                        {
                            "id": "case",
                            "prompt": "Use the fixture",
                            "assertions": ["Fixture is used"],
                            "files": [
                                {
                                    "source": "evals/files/project/config.txt",
                                    "dest": "config/settings.txt",
                                }
                            ],
                        }
                    ],
                }
            )
        )
        self.assertEqual(MODULE.check_evals(path), [])

    def test_rejects_malformed_setup_commands(self):
        path = self.write_spec(
            {
                "id": "case",
                "prompt": "Do the thing",
                "assertions": ["Output is correct"],
                "setup": "printf fixture > input.txt",
            }
        )
        self.assertTrue(any("'setup'" in error for error in MODULE.check_evals(path)))

    def test_trigger_probe_requires_boolean_expectation_when_present(self):
        self.tempdir = tempfile.TemporaryDirectory()
        skill = Path(self.tempdir.name) / "sample"
        evals = skill / "evals"
        evals.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text("# Sample\n")
        path = evals / "evals.json"
        spec = {
            "skill_name": "sample",
            "evals": [
                {
                    "id": "case",
                    "prompt": "Do the thing",
                    "assertions": ["Output is correct"],
                }
            ],
            "trigger_probes": [
                {
                    "id": "negative",
                    "prompt": "Unrelated request",
                    "fingerprints": ["sample-only-phrase"],
                    "expect_activation": "no",
                }
            ],
        }
        path.write_text(json.dumps(spec))
        self.assertTrue(
            any("expect_activation" in error for error in MODULE.check_evals(path))
        )


if __name__ == "__main__":
    unittest.main()
