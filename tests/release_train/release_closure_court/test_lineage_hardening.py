"""Adversarial hardening of the lineage / scope / dependency laws (PR #282).

Chicago style: every test runs the real court (``evaluate`` / ``repair_order`` / the CLI)
on real closure dicts or files and asserts on the returned verdict. The two reference
implementations below are the PR's original (pre-hardening) algorithms, kept verbatim as
differential oracles: the hardened, linear-time versions must agree with them on every
input the originals could handle.
"""

from __future__ import annotations

import copy
import io
import json
import random
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from scripts.release_train.release_closure_court import court
from scripts.release_train.release_closure_court.__main__ import main
from scripts.release_train.release_closure_court.bench import synthetic_closure
from scripts.release_train.release_closure_court.court import evaluate, repair_order

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_court import B, C, _base, _with_lineage

ROOT = Path(__file__).resolve().parents[3]
BENCH_RECEIPT = ROOT / "benchmarks" / "release-closure-court" / "v1" / "receipt.json"


def _reference_repair_order(rows: list[dict[str, Any]], remaining_ids: set[str]) -> list[str]:
    graph: dict[str, list[str]] = {}
    for r in rows:
        deps = r.get("depends_on", [])
        graph[r.get("subject_id")] = [d for d in deps if isinstance(d, str)] if isinstance(deps, list) else []
    dependents: dict[str, set[str]] = {}
    for sid, deps in graph.items():
        for dep in deps:
            dependents.setdefault(dep, set()).add(sid)

    def reach(sid: str) -> int:
        seen: set[str] = set()
        stack = list(dependents.get(sid, ()))
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                stack.extend(dependents.get(node, ()))
        return len(seen)

    weight = {sid: reach(sid) for sid in remaining_ids}
    order: list[str] = []
    done: set[str] = set()
    while len(done) < len(remaining_ids):
        ready = [
            sid
            for sid in remaining_ids
            if sid not in done and all(d in done or d not in remaining_ids for d in graph.get(sid, []))
        ]
        if not ready:
            ready = [sid for sid in remaining_ids if sid not in done]
        nxt = min(ready, key=lambda sid: (-weight[sid], str(sid)))
        order.append(nxt)
        done.add(nxt)
    return order


def _reference_dependency_refusals(rows: list[dict[str, Any]]) -> list[str]:
    ids = {r.get("subject_id") for r in rows}
    out: list[str] = []
    graph: dict[str, list[str]] = {}
    for row in rows:
        sid = row.get("subject_id")
        deps = row.get("depends_on", [])
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            out.append(f"REFUSED:MALFORMED_ROW:{sid}:depends_on")
            continue
        for dep in deps:
            if dep not in ids or dep == sid:
                out.append(f"REFUSED:DEPENDENCY_NOT_ADMITTED:{sid}:{dep}")
        graph[sid] = [d for d in deps if d in ids and d != sid]
    state: dict[str, int] = {}

    def visit(node: str) -> None:
        state[node] = 1
        for dep in graph.get(node, []):
            if state.get(dep) == 1:
                out.append(f"REFUSED:DEPENDENCY_CYCLE:{node}->{dep}")
            elif dep not in state:
                visit(dep)
        state[node] = 2

    for node in sorted(graph, key=str):
        if node not in state:
            visit(node)
    return out


def _random_rows(rng: random.Random) -> list[dict[str, Any]]:
    n = rng.randint(1, 14)
    ids = [f"N{i}" for i in range(n)]
    rows = []
    for sid in ids:
        deps = [rng.choice(ids + ["GHOST"]) for _ in range(rng.randint(0, 4))]
        rows.append({"subject_id": sid, "depends_on": deps})
    rng.shuffle(rows)
    return rows


def _refusals(closure: Any) -> tuple[str, ...]:
    return evaluate(closure).refusals


class DifferentialOracleTests(unittest.TestCase):
    def test_repair_order_matches_reference_on_random_graphs_with_cycles(self) -> None:
        rng = random.Random(282)
        for trial in range(600):
            rows = _random_rows(rng)
            ids = [r["subject_id"] for r in rows]
            remaining = set(rng.sample(ids, rng.randint(0, len(ids))))
            with self.subTest(trial=trial):
                self.assertEqual(repair_order(rows, remaining), _reference_repair_order(rows, remaining))

    def test_dependency_refusals_match_recursive_reference(self) -> None:
        rng = random.Random(26926)
        for trial in range(600):
            rows = _random_rows(rng)
            with self.subTest(trial=trial):
                self.assertEqual(court._dependency_refusals(rows), _reference_dependency_refusals(rows))


class FailClosedLineageTests(unittest.TestCase):
    def _assert_refused(self, closure: dict, prefix: str) -> None:
        refusals = _refusals(closure)
        self.assertTrue(any(r.startswith(prefix) for r in refusals), refusals)
        self.assertEqual(evaluate(closure).standing, "REFUSED")

    def test_canonical_without_additions_under_bound_is_refused(self) -> None:
        c = _with_lineage()
        del c["subjects"][1]["lineage"][0]["additions"]
        self._assert_refused(c, "REFUSED:SCOPE_EXCEEDS_BOUND:IMPL:pr=7:additions=UNKNOWN")

    def test_canonical_without_additions_and_no_bound_is_admitted(self) -> None:
        c = _with_lineage()
        del c["max_canonical_additions"]
        del c["subjects"][1]["lineage"][0]["additions"]
        self.assertEqual(evaluate(c).standing, "ALIVE")

    def test_non_integer_or_negative_additions_are_malformed(self) -> None:
        for bad in ("999999", -1, True, 1.5, None):
            with self.subTest(additions=bad):
                c = _with_lineage()
                c["subjects"][1]["lineage"][0]["additions"] = bad
                self._assert_refused(c, "REFUSED:MALFORMED_ROW:IMPL:lineage[0]")

    def test_bound_exactly_met_is_admitted_and_one_over_is_refused(self) -> None:
        c = _with_lineage()
        _ = c["subjects"][1]["lineage"][0].update(additions=50000)
        self.assertEqual(evaluate(c).standing, "ALIVE")
        c["subjects"][1]["lineage"][0]["additions"] = 50001
        self._assert_refused(c, "REFUSED:SCOPE_EXCEEDS_BOUND:IMPL:pr=7:additions=50001>50000")

    def test_malformed_bound_is_refused(self) -> None:
        for bad in (-1, "50000", True, 1.0):
            with self.subTest(bound=bad):
                c = _with_lineage()
                c["max_canonical_additions"] = bad
                self._assert_refused(c, "REFUSED:MALFORMED_ROW:closure:max_canonical_additions")

    def test_lineage_with_zero_canonical_heads_is_ambiguous(self) -> None:
        c = _with_lineage()
        c["subjects"][1]["lineage"][0]["disposition"] = "SUPERSEDED"
        self._assert_refused(c, "REFUSED:SUCCESSOR_AMBIGUOUS:IMPL:canonical=0")

    def test_empty_lineage_declares_no_prs_and_is_admitted(self) -> None:
        c = _with_lineage()
        c["subjects"][1]["lineage"] = []
        self.assertEqual(evaluate(c).standing, "ALIVE")

    def test_duplicate_delivery_of_one_pr_is_malformed(self) -> None:
        c = _with_lineage()
        c["subjects"][1]["lineage"].append(copy.deepcopy(c["subjects"][1]["lineage"][0]))
        self._assert_refused(c, "REFUSED:MALFORMED_ROW:IMPL:lineage[2]:duplicate-pr=7")

    def test_one_pr_claimed_as_canonical_and_superseded_is_malformed(self) -> None:
        c = _with_lineage()
        c["subjects"][1]["lineage"][1]["pr"] = 7
        self._assert_refused(c, "REFUSED:MALFORMED_ROW:IMPL:lineage[1]:duplicate-pr=7")

    def test_non_positive_or_bool_pr_numbers_are_malformed(self) -> None:
        for bad in (0, -7, True, "7", 7.0):
            with self.subTest(pr=bad):
                c = _with_lineage()
                c["subjects"][1]["lineage"][0]["pr"] = bad
                self._assert_refused(c, "REFUSED:MALFORMED_ROW:IMPL:lineage[0]")

    def test_draft_must_be_bool_and_merged_is_never_draft(self) -> None:
        for field, value in (("draft", "no"), ("draft", 0), ("draft", True)):
            with self.subTest(value=value):
                c = _with_lineage()
                c["subjects"][1]["lineage"][0][field] = value
                self._assert_refused(c, "REFUSED:MALFORMED_ROW:IMPL:lineage[0]")

    def test_stale_subject_canonical_head_behind_row_sha_is_split(self) -> None:
        c = _with_lineage()
        c["subjects"][1]["lineage"][0]["sha"] = C
        self._assert_refused(c, "REFUSED:CANONICAL_SUBJECT_SPLIT:IMPL:pr=7")

    def test_uppercase_or_short_sha_is_malformed(self) -> None:
        for bad in (B.upper(), B[:39], B + "0", "g" * 40):
            with self.subTest(sha=bad):
                c = _with_lineage()
                c["subjects"][1]["lineage"][0]["sha"] = bad
                self._assert_refused(c, "REFUSED:MALFORMED_ROW:IMPL:lineage[0]")

    def test_unknown_state_or_disposition_is_malformed(self) -> None:
        for field, value in (("state", "merged"), ("state", None), ("disposition", "canonical")):
            with self.subTest(field=field, value=value):
                c = _with_lineage()
                c["subjects"][1]["lineage"][0][field] = value
                self._assert_refused(c, "REFUSED:MALFORMED_ROW:IMPL:lineage[0]")


class StructuralInputTests(unittest.TestCase):
    def test_unhashable_subject_id_is_refused_not_a_crash(self) -> None:
        for bad in (["X"], {"x": 1}):
            with self.subTest(sid=bad):
                c = _with_lineage()
                c["subjects"][1]["subject_id"] = bad
                self.assertIn(f"REFUSED:MALFORMED_ROW:{bad}:subject_id", _refusals(c))

    def test_duplicate_unhashable_subject_ids_are_reported_once(self) -> None:
        c = _base()
        c["subjects"][0]["subject_id"] = ["X"]
        c["subjects"][1]["subject_id"] = ["X"]
        self.assertEqual([r for r in _refusals(c) if "DUPLICATE_SUBJECT_ID" in r],
                         ["REFUSED:DUPLICATE_SUBJECT_ID:['X']"])

    def test_non_object_rows_closure_and_subjects_are_refused(self) -> None:
        c = _base()
        c["subjects"].append("row")
        self.assertIn("REFUSED:MALFORMED_ROW:subjects[2]:row", _refusals(c))
        self.assertIn("REFUSED:MALFORMED_ROW:closure:not-an-object", _refusals([1, 2]))
        self.assertIn("REFUSED:MALFORMED_ROW:closure:subjects-not-a-list", _refusals({"subjects": {"a": 1}}))

    def test_cli_refuses_a_malformed_file_with_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp, "bad.json")
            bad.write_text(json.dumps({"subjects": ["x", 3]}), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(main(["court", str(bad)]), 2)
            self.assertEqual(json.loads(buf.getvalue())["standing"], "REFUSED")

    def test_long_dependency_chain_has_no_recursion_ceiling(self) -> None:
        closure = synthetic_closure(sys.getrecursionlimit() * 3)
        verdict = evaluate(closure)
        self.assertEqual(verdict.standing, "PARTIAL_ALIVE", verdict.refusals[:3])
        order = verdict.receipt["repair_order"]
        self.assertEqual(order[0], closure["subjects"][-1]["subject_id"])
        self.assertEqual(order[-1], closure["subjects"][0]["subject_id"])

    def test_long_cycle_is_refused_once(self) -> None:
        closure = synthetic_closure(2500)
        closure["subjects"][-1]["depends_on"] = [closure["subjects"][0]["subject_id"]]
        cycles = [r for r in _refusals(closure) if r.startswith("REFUSED:DEPENDENCY_CYCLE")]
        self.assertEqual(len(cycles), 1, cycles)


class ReplayAndReorderingTests(unittest.TestCase):
    def test_receipt_is_invariant_under_row_and_lineage_reordering(self) -> None:
        rng = random.Random(7)
        base = synthetic_closure(60)
        base["subjects"][10]["impl_standing"] = "ALIVE"
        base["subjects"][10]["courts"] = [{"court": "ci", "result": "PASS", "sha": base["subjects"][10]["sha"]}]
        base["subjects"][20]["lineage"][1]["state"] = "OPEN"  # one refusal in the mix
        expected = evaluate(base).receipt
        for trial in range(25):
            shuffled = copy.deepcopy(base)
            rng.shuffle(shuffled["subjects"])
            for row in shuffled["subjects"]:
                rng.shuffle(row["lineage"])
            with self.subTest(trial=trial):
                self.assertEqual(evaluate(shuffled).receipt, expected)

    def test_replay_of_the_same_closure_is_byte_identical(self) -> None:
        closure = synthetic_closure(200)
        first = json.dumps(evaluate(closure).receipt, sort_keys=True)
        second = json.dumps(evaluate(json.loads(json.dumps(closure))).receipt, sort_keys=True)
        self.assertEqual(first, second)

    def test_unauthorized_authority_claim_still_refused_on_lineage_rows(self) -> None:
        c = _with_lineage()
        c["subjects"][1]["authority_claimed"] = "DO"
        self.assertIn("REFUSED:AUTHORITY_ESCALATION:IMPL:DO>CONSTRUCT", _refusals(c))


class BenchmarkRegressionTests(unittest.TestCase):
    """Regression bound on evaluation time. The PR's original algorithm was quadratic
    (483 ms median at n=900 on the recording machine, RecursionError at n=3000); the bound
    below admits the hardened linear-time court with a 10x margin over the committed receipt
    and refuses a quadratic regression."""

    def test_committed_bench_receipt_records_replayable_linear_numbers(self) -> None:
        receipt = json.loads(BENCH_RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(receipt["authority"], "NONE")
        rows = {r["n"]: r for r in receipt["after"]["results"]}
        self.assertTrue(all(r["replay_identical"] for r in rows.values()))
        self.assertLess(rows[4000]["evaluate_median_ms"], receipt["regression_bound_ms"]["n4000"])

    def test_evaluate_4000_row_chain_within_bound(self) -> None:
        receipt = json.loads(BENCH_RECEIPT.read_text(encoding="utf-8"))
        closure = synthetic_closure(4000)
        best = float("inf")
        for _ in range(3):
            t0 = time.perf_counter()
            evaluate(closure)
            best = min(best, (time.perf_counter() - t0) * 1000.0)
        self.assertLess(best, receipt["regression_bound_ms"]["n4000"], f"{best:.1f} ms")


if __name__ == "__main__":
    unittest.main()
