#!/usr/bin/env python3
"""Tests for binary skill-eval scoring and judge verdict parsing."""

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eval_scoring import aggregate_reps, parse_judge_verdict, trigger_metrics


class ScoringTests(unittest.TestCase):
    def test_parses_split_output_and_process_scores(self):
        verdict = parse_judge_verdict(
            "\n".join(
                [
                    "A-OUTPUT: 2",
                    "A-PROCESS: 1",
                    "B-OUTPUT: 1",
                    "B-PROCESS: 0",
                    "A-PASS: 3",
                    "B-PASS: 1",
                ]
            ),
            output_assertions=2,
            process_assertions=1,
        )
        self.assertEqual(verdict["a_total"], 3)
        self.assertEqual(verdict["b_total"], 1)

    def test_parses_list_form_verdicts_judges_naturally_write(self):
        verdict = parse_judge_verdict(
            "\n".join(
                [
                    "A-OUTPUT: 1, 2, 3",
                    "A-PROCESS: 1, 2",
                    "B-OUTPUT: 2, 3",
                    "B-PROCESS: 1, 2",
                    "A-PASS: 5",
                    "B-PASS: 4",
                ]
            ),
            output_assertions=3,
            process_assertions=2,
        )
        self.assertEqual(verdict["a_output"], 3)
        self.assertEqual(verdict["a_process"], 2)
        self.assertEqual(verdict["a_total"], 5)
        self.assertEqual(verdict["b_total"], 4)

    def test_rejects_out_of_range_or_inconsistent_verdict(self):
        with self.assertRaises(ValueError):
            parse_judge_verdict(
                "A-OUTPUT: 3\nA-PROCESS: 0\nB-OUTPUT: 0\nB-PROCESS: 0\nA-PASS: 2\nB-PASS: 0",
                output_assertions=2,
                process_assertions=1,
            )
        with self.assertRaises(ValueError):
            parse_judge_verdict(
                "A-OUTPUT: 1\nA-PROCESS: 0\nB-OUTPUT: 0\nB-PROCESS: 0\nA-PASS: 2\nB-PASS: 0",
                output_assertions=2,
                process_assertions=0,
            )

    def test_trigger_metrics_distinguish_positive_and_negative_probes(self):
        positive = trigger_metrics(
            reps=5,
            expect_activation=True,
            fingerprint_hits=4,
            control_fingerprint_hits=1,
            skill_reads=5,
            control_skill_reads=0,
        )
        self.assertEqual(positive["skill_miss_rate"], 0.0)
        self.assertEqual(positive["control_skill_read_rate"], 0.0)

        negative = trigger_metrics(
            reps=4,
            expect_activation=False,
            fingerprint_hits=1,
            control_fingerprint_hits=0,
            skill_reads=1,
            control_skill_reads=0,
        )
        self.assertEqual(negative["false_positive_rate"], 0.25)
        self.assertEqual(negative["fingerprint_false_positive_rate"], 0.25)
        self.assertEqual(negative["control_skill_read_rate"], 0.0)

    def test_aggregate_keeps_binary_tasks_and_assertion_detail(self):
        result = aggregate_reps(
            [
                {
                    "output_assertions": 2,
                    "process_assertions": 1,
                    "with_output": 2,
                    "with_process": 1,
                    "without_output": 1,
                    "without_process": 0,
                    "with_pass": True,
                    "without_pass": False,
                },
                {
                    "output_assertions": 2,
                    "process_assertions": 1,
                    "with_output": 1,
                    "with_process": 1,
                    "without_output": 1,
                    "without_process": 1,
                    "with_pass": True,
                    "without_pass": True,
                },
            ]
        )
        self.assertEqual(result["with_task_passes"], 2)
        self.assertEqual(result["without_task_passes"], 1)
        self.assertEqual(result["with_assertion_points"], 5)
        self.assertEqual(result["without_assertion_points"], 3)
        self.assertEqual(result["max_task_passes"], 2)
        self.assertEqual(result["with_total"], 5)
        self.assertEqual(result["without_total"], 3)
        self.assertEqual(result["lift"], 2)


if __name__ == "__main__":
    unittest.main()
