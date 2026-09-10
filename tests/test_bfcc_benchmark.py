"""Tests for scripts/bfcc_benchmark.py.

Chicago-style: real JSONL fixture files written to disk in a tempdir (actual file
I/O), real subprocess-free direct calls into the module under test, state-based
assertions on real return values. No interaction-based test doubles of any kind.
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import bfcc_benchmark  # noqa: E402


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def receipt(problem_class: str, delta: float, resource_total: float = 10.0, **extra) -> dict:
    return {
        "subject": "test-subject",
        "problem_class": problem_class,
        "resource_vector": {
            "human_reasoning": resource_total,
            "model_tokens": 0,
            "novel_code": 0,
            "compute": 0,
            "time": 0,
            "dependencies": 0,
        },
        "verified_capability_delta": delta,
        **extra,
    }


class ImprovingDirectionTest(unittest.TestCase):
    def test_slope_positive_hand_computed(self) -> None:
        # resource_total=10 for every receipt -> eta = delta/10 = 1, 2, 3
        # x = 0, 1, 2 (equally spaced) -> OLS slope = 1.0 exactly
        rows = [
            receipt("cls-improving", 10.0),
            receipt("cls-improving", 20.0),
            receipt("cls-improving", 30.0),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "receipts.jsonl"
            write_jsonl(path, rows)
            receipts = bfcc_benchmark.load_receipts(path)
            self.assertEqual(len(receipts), 3)
            report = bfcc_benchmark.benchmark(receipts)
            entry = report["cls-improving"]["eta"]
            self.assertEqual(entry["values"], [1.0, 2.0, 3.0])
            self.assertEqual(entry["direction"], "IMPROVING")
            self.assertAlmostEqual(entry["slope"], 1.0, places=9)


class DegradingDirectionTest(unittest.TestCase):
    def test_slope_negative_hand_computed(self) -> None:
        # eta = 30/10, 20/10, 10/10 = 3, 2, 1 -> OLS slope = -1.0 exactly
        rows = [
            receipt("cls-degrading", 30.0),
            receipt("cls-degrading", 20.0),
            receipt("cls-degrading", 10.0),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "receipts.jsonl"
            write_jsonl(path, rows)
            receipts = bfcc_benchmark.load_receipts(path)
            report = bfcc_benchmark.benchmark(receipts)
            entry = report["cls-degrading"]["eta"]
            self.assertEqual(entry["values"], [3.0, 2.0, 1.0])
            self.assertEqual(entry["direction"], "DEGRADING")
            self.assertAlmostEqual(entry["slope"], -1.0, places=9)


class FlatDirectionTest(unittest.TestCase):
    def test_slope_zero_hand_computed(self) -> None:
        # eta = 1, 1, 1, 1 for every receipt -> OLS slope = 0.0 exactly
        rows = [receipt("cls-flat", 10.0) for _ in range(4)]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "receipts.jsonl"
            write_jsonl(path, rows)
            receipts = bfcc_benchmark.load_receipts(path)
            report = bfcc_benchmark.benchmark(receipts)
            entry = report["cls-flat"]["eta"]
            self.assertEqual(entry["values"], [1.0, 1.0, 1.0, 1.0])
            self.assertEqual(entry["direction"], "FLAT")
            self.assertAlmostEqual(entry["slope"], 0.0, places=9)


class InsufficientDataDirectionTest(unittest.TestCase):
    def test_single_receipt_is_insufficient(self) -> None:
        rows = [receipt("cls-single", 10.0)]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "receipts.jsonl"
            write_jsonl(path, rows)
            receipts = bfcc_benchmark.load_receipts(path)
            report = bfcc_benchmark.benchmark(receipts)
            entry = report["cls-single"]["eta"]
            self.assertEqual(entry["direction"], "INSUFFICIENT_DATA")
            self.assertIsNone(entry["slope"])

    def test_zero_receipts_for_class_never_appear(self) -> None:
        # A problem_class with 0 matching receipts simply never appears in the
        # report keyed by problem_class -- but no class that DOES appear with
        # receipts is ever silently omitted or given a fifth direction value.
        rows = [receipt("cls-a", 10.0), receipt("cls-a", 20.0)]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "receipts.jsonl"
            write_jsonl(path, rows)
            receipts = bfcc_benchmark.load_receipts(path)
            report = bfcc_benchmark.benchmark(receipts)
            self.assertIn("cls-a", report)
            for entry in report.values():
                self.assertIn(entry["eta"]["direction"], bfcc_benchmark.DIRECTIONS)
                self.assertIn(entry["lambda"]["direction"], bfcc_benchmark.DIRECTIONS)


class LambdaTrimtabLeverageTest(unittest.TestCase):
    def test_lambda_uses_canonical_information_delta_when_present(self) -> None:
        # canonical_information_delta = 10, 20, 30 with resource_total=10 ->
        # lambda = 1, 2, 3 -> OLS slope = 1.0 exactly (same shape as eta improving)
        rows = [
            receipt("cls-lambda", 5.0, canonical_information_delta=10.0),
            receipt("cls-lambda", 5.0, canonical_information_delta=20.0),
            receipt("cls-lambda", 5.0, canonical_information_delta=30.0),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "receipts.jsonl"
            write_jsonl(path, rows)
            receipts = bfcc_benchmark.load_receipts(path)
            report = bfcc_benchmark.benchmark(receipts)
            entry = report["cls-lambda"]["lambda"]
            self.assertEqual(entry["values"], [1.0, 2.0, 3.0])
            self.assertEqual(entry["direction"], "IMPROVING")
            self.assertAlmostEqual(entry["slope"], 1.0, places=9)

    def test_lambda_insufficient_when_canonical_information_delta_absent(self) -> None:
        rows = [receipt("cls-no-lambda", 10.0), receipt("cls-no-lambda", 20.0)]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "receipts.jsonl"
            write_jsonl(path, rows)
            receipts = bfcc_benchmark.load_receipts(path)
            report = bfcc_benchmark.benchmark(receipts)
            entry = report["cls-no-lambda"]["lambda"]
            self.assertEqual(entry["direction"], "INSUFFICIENT_DATA")
            self.assertEqual(entry["values"], [])


class MissingOrEmptyLedgerTest(unittest.TestCase):
    def test_missing_ledger_file_reports_insufficient_data_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "does-not-exist.jsonl"
            receipts = bfcc_benchmark.load_receipts(missing_path)
            self.assertEqual(receipts, [])
            report = bfcc_benchmark.benchmark(receipts)
            self.assertEqual(report, {})

    def test_empty_ledger_file_reports_insufficient_data_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_path = Path(tmpdir) / "empty.jsonl"
            empty_path.write_text("", encoding="utf-8")
            receipts = bfcc_benchmark.load_receipts(empty_path)
            self.assertEqual(receipts, [])
            report = bfcc_benchmark.benchmark(receipts)
            self.assertEqual(report, {})

    def test_dev_null_via_main_does_not_crash(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = bfcc_benchmark.main(["--receipts", "/dev/null", "--json"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload, {"problem_classes": {}})

    def test_nonexistent_path_via_main_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "nope.jsonl"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = bfcc_benchmark.main(["--receipts", str(missing_path), "--json"])
            self.assertEqual(exit_code, 0)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(payload, {"problem_classes": {}})


class LeastSquaresSlopeArithmeticTest(unittest.TestCase):
    def test_known_three_point_series(self) -> None:
        # y = 2, 4, 6 at x = 0, 1, 2: mean_x=1, mean_y=4
        # numerator = (-1)(-2) + (0)(0) + (1)(2) = 2 + 0 + 2 = 4
        # denominator = 1 + 0 + 1 = 2 -> slope = 2.0
        self.assertAlmostEqual(bfcc_benchmark.least_squares_slope([2.0, 4.0, 6.0]), 2.0, places=9)

    def test_noisy_series_hand_computed(self) -> None:
        # y = 1, 3, 2, 5 at x = 0,1,2,3: mean_x=1.5, mean_y=2.75
        # deviations x: -1.5,-0.5,0.5,1.5 ; y: -1.75,0.25,-0.75,2.25
        # numerator = (-1.5*-1.75)+(-0.5*0.25)+(0.5*-0.75)+(1.5*2.25)
        #           = 2.625 - 0.125 - 0.375 + 3.375 = 5.5
        # denominator = 2.25+0.25+0.25+2.25 = 5.0 -> slope = 1.1
        self.assertAlmostEqual(
            bfcc_benchmark.least_squares_slope([1.0, 3.0, 2.0, 5.0]), 1.1, places=9
        )


if __name__ == "__main__":
    unittest.main()
