#!/usr/bin/env python3
"""Unit tests for deterministic skill-eval fingerprints."""

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from skill_eval_utils import (
    build_compliance_record,
    build_trigger_record,
    hash_profile_runtime,
    prepare_isolated_arms,
)


class FingerprintTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.skills = self.root / "skills"
        self.skill = self.skills / "sample"
        (self.skill / "evals" / "files").mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("# Sample\n\nDo the thing.\n")
        (self.skill / "evals" / "other.json").write_text('{"other": true}\n')
        fixture = self.skill / "evals" / "files" / "input.txt"
        fixture.write_text("original fixture\n")

        self.loaded = self.skills / "helper"
        self.loaded.mkdir()
        (self.loaded / "SKILL.md").write_text("# Helper\n")

        self.runner = self.root / "runner.py"
        self.runner.write_text("# runner v1\n")
        self.runner_files = {"runner.py": self.runner}
        self.eval_spec = {
            "id": "does-the-thing",
            "prompt": "Do the thing.",
            "files": ["evals/files/input.txt"],
            "assertions": ["The response does the thing."],
        }
        self.probe_spec = {
            "id": "fires-on-thing",
            "prompt": "Please do the thing.",
            "fingerprints": ["thing-specific-phrase"],
        }
        self.config = {
            "provider": "test-provider",
            "model": "test-model",
            "judge_provider": "test-provider",
            "judge_model": "test-model",
            "pi_version": "test-pi 1.0",
            "timeout_seconds": 300,
            "repetitions": 5,
        }

    def tearDown(self):
        self.tempdir.cleanup()

    def compliance(self):
        return build_compliance_record(
            "sample",
            self.skill,
            self.eval_spec,
            {"helper": self.loaded},
            self.runner_files,
            self.config,
        )

    def trigger(self):
        return build_trigger_record(
            "sample",
            self.skills,
            self.probe_spec,
            self.runner_files,
            self.config,
        )

    def test_object_fixture_entries_preserve_destination_layout(self):
        nested = self.skill / "evals" / "files" / "project" / "config.txt"
        nested.parent.mkdir(parents=True)
        nested.write_text("nested fixture\n")
        spec = {
            **self.eval_spec,
            "files": [
                {
                    "source": "evals/files/project/config.txt",
                    "dest": "config/settings.txt",
                }
            ],
        }
        arms = prepare_isolated_arms(
            self.root / "run",
            self.skill,
            spec["files"],
            ("treatment", "control"),
            "eval",
        )
        for arm in arms.values():
            self.assertEqual(
                (arm.workdir / "config" / "settings.txt").read_text(),
                "nested fixture\n",
            )
        record = build_compliance_record(
            "sample",
            self.skill,
            spec,
            {"helper": self.loaded},
            self.runner_files,
            self.config,
        )
        self.assertEqual(record, record)

    def test_fingerprint_is_deterministic(self):
        self.assertEqual(self.compliance(), self.compliance())
        self.assertEqual(self.trigger(), self.trigger())

    def test_skill_definition_and_config_changes_are_separated(self):
        before = self.compliance()
        (self.skill / "SKILL.md").write_text("# Sample\n\nDo it better.\n")
        after_skill = self.compliance()

        self.assertNotEqual(
            before["fingerprints"]["content"],
            after_skill["fingerprints"]["content"],
        )
        self.assertEqual(
            before["fingerprints"]["config"],
            after_skill["fingerprints"]["config"],
        )

        changed_config = {**self.config, "model": "another-model"}
        after_config = build_compliance_record(
            "sample",
            self.skill,
            self.eval_spec,
            {"helper": self.loaded},
            self.runner_files,
            changed_config,
        )
        self.assertEqual(
            after_skill["fingerprints"]["content"],
            after_config["fingerprints"]["content"],
        )
        self.assertNotEqual(
            after_skill["fingerprints"]["config"],
            after_config["fingerprints"]["config"],
        )

    def test_unrelated_eval_file_does_not_invalidate_one_case(self):
        before = self.compliance()
        (self.skill / "evals" / "other.json").write_text('{"other": false}\n')
        self.assertEqual(before, self.compliance())

    def test_case_fixture_and_trigger_catalog_changes_invalidate_content(self):
        before = self.compliance()
        (self.skill / "evals" / "files" / "input.txt").write_text("changed\n")
        after_fixture = self.compliance()
        self.assertNotEqual(
            before["fingerprints"]["content"],
            after_fixture["fingerprints"]["content"],
        )

        before_trigger = self.trigger()
        (self.loaded / "SKILL.md").write_text("# Helper\n\nChanged catalog text.\n")
        after_catalog = self.trigger()
        self.assertNotEqual(
            before_trigger["fingerprints"]["content"],
            after_catalog["fingerprints"]["content"],
        )

    def test_runner_change_invalidates_combined_fingerprint(self):
        before = self.compliance()
        self.runner.write_text("# runner v2\n")
        after = self.compliance()
        self.assertNotEqual(
            before["fingerprints"]["runner"],
            after["fingerprints"]["runner"],
        )
        self.assertNotEqual(
            before["fingerprints"]["combined"],
            after["fingerprints"]["combined"],
        )

    def test_profile_runtime_hash_excludes_auth_and_tracks_settings(self):
        profile = self.root / "profile"
        profile.mkdir()
        (profile / "settings.json").write_text('{"theme":"light"}\n')
        (profile / "AGENTS.md").write_text("shared instructions\n")
        (profile / "auth.json").write_text('{"token":"first"}\n')

        before = hash_profile_runtime(profile)
        (profile / "auth.json").write_text('{"token":"rotated"}\n')
        self.assertEqual(before, hash_profile_runtime(profile))

        (profile / "settings.json").write_text('{"theme":"dark"}\n')
        self.assertNotEqual(before, hash_profile_runtime(profile))

    def test_profile_runtime_hash_uses_symlink_target_content(self):
        fingerprints = []
        for name in ("one", "two"):
            shared = self.root / f"shared-{name}"
            shared.mkdir()
            (shared / "package.json").write_text('{"name":"shared"}\n')
            profile = self.root / f"profile-{name}"
            profile.mkdir()
            (profile / "settings.json").write_text('{"theme":"light"}\n')
            (profile / "npm").symlink_to(shared, target_is_directory=True)
            fingerprints.append(hash_profile_runtime(profile))
        self.assertEqual(fingerprints[0], fingerprints[1])


if __name__ == "__main__":
    unittest.main()
