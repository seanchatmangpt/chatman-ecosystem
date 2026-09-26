"""Regression-bound law of benchmarks/root_crown/bench_term_u.py (no timing here).

Chicago style: the real ``regressions`` function over the real committed bench receipt and
real edited copies of it. The timing itself runs in CI via ``bench_term_u.py --check``.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "benchmarks/root_crown"))

import bench_term_u as bench  # noqa: E402

CASES = {"release_terms", "validate_requirements", "autonomic_receipt", "crown_evaluate"}


class BenchReceiptTest(unittest.TestCase):
    def setUp(self):
        self.recorded = json.loads(bench.RECEIPT.read_text(encoding="utf-8"))

    def test_committed_receipt_covers_every_case(self):
        self.assertEqual(self.recorded["schema"], bench.SCHEMA)
        self.assertEqual(set(self.recorded["cases"]), CASES)
        self.assertEqual(self.recorded["authority"], "NONE")
        for case in self.recorded["cases"].values():
            self.assertGreater(case["median_s"], 0)
            self.assertLessEqual(case["min_s"], case["median_s"])

    def test_identical_measurement_is_within_bound(self):
        self.assertEqual(bench.regressions(self.recorded, copy.deepcopy(self.recorded)), [])

    def test_slowdown_past_the_factor_is_a_regression(self):
        slow = copy.deepcopy(self.recorded)
        rec = self.recorded["cases"]["crown_evaluate"]["median_s"]
        slow["cases"]["crown_evaluate"]["median_s"] = rec * self.recorded["regression_factor"] * 1.01 + 1
        found = bench.regressions(self.recorded, slow)
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0].startswith("crown_evaluate:"), found)

    def test_floor_absorbs_sub_millisecond_noise(self):
        noisy = copy.deepcopy(self.recorded)
        noisy["cases"]["release_terms"]["median_s"] = self.recorded["floor_s"]
        self.assertEqual(bench.regressions(self.recorded, noisy), [])

    def test_missing_case_is_a_regression(self):
        partial = copy.deepcopy(self.recorded)
        del partial["cases"]["autonomic_receipt"]
        self.assertEqual(bench.regressions(self.recorded, partial), ["autonomic_receipt: case missing"])


if __name__ == "__main__":
    unittest.main()
