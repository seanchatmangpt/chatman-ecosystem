"""The mutation harness itself: refusals, survivor accounting, exit codes, committed report.

Chicago style: each test writes a real, tiny package and a real unittest suite to a temp
directory and runs the real harness over it (``mutate.run`` / ``mutate.main``); nothing is
faked. The full root-crown mutant set is not re-run here (that is the CI step
``python3 -m scripts.release_train.root_crown.mutate --check-report``); this module only
checks that every committed anchor still matches exactly once and that the committed report
records zero survivors.
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from _support import REPO

from scripts.release_train.root_crown import mutate

CALC = "def add(a, b):\n    return a + b\n"
SUITE = """import unittest

from pkgx.calc import add


class CalcTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), {expected})
"""


def synthetic(root: Path, expected: int = 5) -> Path:
    (root / "pkgx").mkdir()
    (root / "pkgx" / "__init__.py").write_text("")
    (root / "pkgx" / "calc.py").write_text(CALC)
    (root / "tsuite").mkdir()
    (root / "tsuite" / "test_calc.py").write_text(SUITE.format(expected=expected))
    return root


def run(root: Path, *mutants: mutate.SourceMutant) -> dict:
    return mutate.run(root, paths=("pkgx", "tsuite"), test_dir="tsuite", source=tuple(mutants), data=())


KILLABLE = mutate.SourceMutant("add_to_sub", "pkgx/calc.py", "return a + b", "return a - b", ("test_calc",))
EQUIVALENT = mutate.SourceMutant("add_commuted", "pkgx/calc.py", "return a + b", "return b + a", ("test_calc",))


class HarnessTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_killed_mutant_is_counted_and_source_is_restored(self):
        report = run(synthetic(self.root), KILLABLE)
        self.assertEqual((report["all_killed"], report["survivors"], report["total"]), (True, [], 1))
        self.assertTrue(report["mutants"]["add_to_sub"]["killed"])
        self.assertIn("test_calc.CalcTest.test_add", report["mutants"]["add_to_sub"]["detail"])
        self.assertEqual(report["baseline"]["tests_run"], 1)
        self.assertEqual((self.root / "pkgx" / "calc.py").read_text(), CALC, "the source tree is never edited")

    def test_synthetic_survivor_is_reported_and_exits_1(self):
        report = run(synthetic(self.root), KILLABLE, EQUIVALENT)
        self.assertFalse(report["all_killed"])
        self.assertEqual(report["survivors"], ["add_commuted"])
        self.assertTrue(report["mutants"]["add_commuted"]["detail"].startswith("SURVIVED"))

    def test_anchor_drift_is_refused_before_any_test_runs(self):
        drifted = mutate.SourceMutant("mul", "pkgx/calc.py", "return a * b", "return a", ("test_calc",))
        with self.assertRaises(mutate.HarnessRefusal) as caught:
            run(synthetic(self.root, expected=999), drifted)  # a red suite: drift must win first
        self.assertEqual(caught.exception.code, "ANCHOR_DRIFT")
        self.assertIn("mul:pkgx/calc.py:anchor-count=0", caught.exception.detail)
        doubled = mutate.SourceMutant("ret", "pkgx/calc.py", "b", "c", ("test_calc",))
        with self.assertRaises(mutate.HarnessRefusal) as caught:
            run(self.root, doubled)
        self.assertIn("anchor-count=2", caught.exception.detail)

    def test_red_baseline_is_refused(self):
        with self.assertRaises(mutate.HarnessRefusal) as caught:
            run(synthetic(self.root, expected=6), KILLABLE)
        self.assertEqual(caught.exception.code, "BASELINE_RED")
        self.assertIn("test_calc.CalcTest.test_add", caught.exception.detail)
        self.assertEqual(caught.exception.as_dict()["failure_class"], "VERIFICATION_FAILURE")

    def emit(self, report, **flags):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = mutate.emit(report, self.root, **flags)
        return code, out.getvalue()

    def test_exit_codes_and_report_check(self):
        killed = run(synthetic(self.root), KILLABLE)
        survived = run(self.root, KILLABLE, EQUIVALENT)
        self.assertEqual(self.emit(killed)[0], 0)
        self.assertEqual(self.emit(survived)[0], 1)
        code, out = self.emit(killed, check=True)
        self.assertEqual(code, 2, "no committed report: drift")
        self.assertIn('"code": "MUTATION_REPORT_DRIFT"', out)
        self.assertEqual(self.emit(killed, write=True)[0], 0)
        self.assertEqual((self.root / mutate.REPORT).read_bytes(), mutate.dump(killed))
        self.assertEqual(self.emit(run(self.root, KILLABLE), check=True)[0], 0, "the report recomputes byte-identically")
        self.assertEqual(self.emit(survived, check=True)[0], 2)


class CommittedReportTest(unittest.TestCase):
    def test_every_committed_anchor_matches_exactly_once(self):
        self.assertEqual(mutate.anchor_refusals(REPO, mutate.SOURCE_MUTANTS), [])

    def test_committed_report_has_zero_survivors(self):
        path = REPO / mutate.REPORT
        if not path.is_file():
            self.skipTest(f"{mutate.REPORT} not committed")
        report = json.loads(path.read_text(encoding="utf-8"))
        names = {m.name for m in mutate.SOURCE_MUTANTS} | {m.name for m in mutate.DATA_MUTANTS}
        self.assertEqual(set(report["mutants"]), names)
        self.assertEqual((report["survivors"], report["all_killed"]), ([], True))
        self.assertTrue(report["baseline"]["ok"])
        for survivor in ("owner_off", "successor_off", "type_off", "terminal_accepts_partial",
                         "typed_terminal_blocked_as_capability"):  # fmt: skip
            self.assertTrue(report["mutants"][survivor]["killed"], survivor)


if __name__ == "__main__":
    unittest.main()
