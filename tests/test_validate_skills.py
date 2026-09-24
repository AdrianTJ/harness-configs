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


class SemanticDependencyTests(unittest.TestCase):
    """Cross-file checks: ledger rows, attribution footers, sibling refs, links."""

    def write_skill(self, name, body, status="local", upstream_url=None):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        skill = root / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(body)
        if upstream_url:
            row = f"| `{name}` | {status} | [up]({upstream_url}) | pin | date | MIT |\n"
        else:
            row = f"| `{name}` | {status} | none | — | — | — |\n"
        self.ledger = {name: {"status": status, "row": row.rstrip("\n")}}
        return skill / "SKILL.md"

    def add_ledger_row(self, name, status="local", upstream_url=None):
        if upstream_url:
            row = f"| `{name}` | {status} | [up]({upstream_url}) | pin | date | MIT |\n"
        else:
            row = f"| `{name}` | {status} | none | — | — | — |\n"
        self.ledger[name] = {"status": status, "row": row.rstrip("\n")}

    def check(self, path):
        return MODULE.check_semantics(path, ledger=self.ledger)

    def tearDown(self):
        tempdir = getattr(self, "tempdir", None)
        if tempdir is not None:
            tempdir.cleanup()

    def test_missing_ledger_row_is_rejected(self):
        path = self.write_skill("orphan", "# Orphan\n")
        self.ledger.clear()
        errors = self.check(path)
        self.assertTrue(any("SOURCES.md" in e for e in errors), errors)

    def test_vendored_skill_without_attribution_footer_is_rejected(self):
        path = self.write_skill(
            "ported", "# Ported\n\nBody with no source.\n",
            status="vendored", upstream_url="https://github.com/x/ported",
        )
        errors = self.check(path)
        self.assertTrue(any("attribution footer" in e for e in errors), errors)

    def test_vendored_skill_with_attribution_footer_passes(self):
        url = "https://github.com/x/ported"
        path = self.write_skill(
            "ported",
            f"# Ported\n\nVendored from [x/ported]({url}) at `abc123`.\n",
            status="vendored", upstream_url=url,
        )
        self.assertEqual(self.check(path), [])

    def test_reference_to_unknown_sibling_skill_is_rejected(self):
        path = self.write_skill(
            "caller", "# Caller\n\nLog it via the `ghost-skill` skill.\n"
        )
        errors = self.check(path)
        self.assertTrue(any("'ghost-skill'" in e for e in errors), errors)

    def test_reference_to_known_sibling_skill_passes(self):
        path = self.write_skill(
            "caller", "# Caller\n\nLog it via the `writer` skill.\n"
        )
        self.add_ledger_row("writer")
        self.assertEqual(self.check(path), [])

    def test_broken_relative_link_is_rejected(self):
        path = self.write_skill(
            "linked", "# Linked\n\nSee [the guide](docs/guide.md).\n"
        )
        errors = self.check(path)
        self.assertTrue(any("relative link" in e for e in errors), errors)

    def test_existing_relative_link_passes(self):
        path = self.write_skill(
            "linked", "# Linked\n\nSee [the guide](guide.md).\n"
        )
        (path.parent / "guide.md").write_text("# Guide\n")
        self.assertEqual(self.check(path), [])

    def test_also_load_unknown_skill_is_rejected(self):
        self.tempdir = tempfile.TemporaryDirectory()
        skill = Path(self.tempdir.name) / "sample"
        evals = skill / "evals"
        evals.mkdir(parents=True)
        (skill / "SKILL.md").write_text("# Sample\n")
        path = evals / "evals.json"
        path.write_text(json.dumps({
            "skill_name": "sample",
            "evals": [{
                "id": "case",
                "prompt": "Do it",
                "assertions": ["Done"],
                "also_load": ["no-such-skill"],
            }],
        }))
        errors = MODULE.check_evals(path)
        self.assertTrue(any("also_load" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
