import copy
import importlib.util
import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_llm_retirement.py"
SPEC = importlib.util.spec_from_file_location("verify_llm_retirement", SCRIPT)
retire = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(retire)


def edge_by_id(doc, edge_id):
    return next(edge for edge in doc["edge"] if edge["id"] == edge_id)


class LlmRetirementMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = retire.load_toml(ROOT / retire.MAP_RELPATH)

    def fresh(self):
        return copy.deepcopy(self.doc)

    def refusals(self, doc):
        return retire.validate_map(doc, ROOT)

    def assertRefused(self, doc, prefix):
        errors = self.refusals(doc)
        self.assertTrue(
            any(error.startswith(prefix) for error in errors),
            f"expected {prefix} in {errors}",
        )

    def test_canonical_map_is_admissible(self):
        self.assertEqual(self.refusals(self.doc), [])

    def test_honest_baseline_has_no_closed_edge(self):
        m = retire.metrics(self.doc)
        self.assertEqual(m["closed"], 0)
        self.assertEqual(m["llm_residue"], m["edges"])
        self.assertEqual(m["ldr"], 1.0)

    # -- ladder evidence -------------------------------------------------

    def test_verified_without_replay_is_insufficient(self):
        doc = self.fresh()
        edge_by_id(doc, "edge:release-graph-admission")["retirement_state"] = "MACHINE_VERIFIED"
        self.assertRefused(doc, "STATE_EVIDENCE_INSUFFICIENT:edge:release-graph-admission")

    def test_evidence_is_cumulative_down_the_ladder(self):
        doc = self.fresh()
        edge = edge_by_id(doc, "edge:ce23-machinery-absent-courts")
        edge["retirement_state"] = "MACHINE_CANDIDATE"
        edge["machine"] = ["scripts/verify_release.py"]
        edge["smallest_falsifier"] = "x"
        errors = self.refusals(doc)
        self.assertIn(
            "STATE_EVIDENCE_INSUFFICIENT:edge:ce23-machinery-absent-courts claims MACHINE_CANDIDATE without prior_art",
            errors,
        )

    def test_retired_requires_fence_and_receipt(self):
        doc = self.fresh()
        edge = edge_by_id(doc, "edge:test-adequacy-judgment")
        edge["retirement_state"] = "LLM_RETIRED"
        edge["equivalence_corpus"] = ["release/v26.9.25/hardening/inputs/mutation-report.json"]
        errors = self.refusals(doc)
        self.assertIn(
            "STATE_EVIDENCE_INSUFFICIENT:edge:test-adequacy-judgment claims LLM_RETIRED without fence",
            errors,
        )
        self.assertIn(
            "STATE_EVIDENCE_INSUFFICIENT:edge:test-adequacy-judgment claims LLM_RETIRED without receipt",
            errors,
        )

    def test_complete_evidence_closes_an_edge(self):
        doc = self.fresh()
        edge = edge_by_id(doc, "edge:test-adequacy-judgment")
        edge["retirement_state"] = "MACHINE_VERIFIED"
        edge["equivalence_corpus"] = ["release/v26.9.25/hardening/inputs/mutation-report.json"]
        self.assertEqual(self.refusals(doc), [])
        self.assertEqual(retire.metrics(doc)["closed"], 1)

    def test_prose_claimed_evidence_path_is_refused(self):
        doc = self.fresh()
        edge_by_id(doc, "edge:release-graph-admission")["machine"] = ["scripts/does_not_exist.py"]
        self.assertRefused(doc, "EVIDENCE_PATH_MISSING:edge:release-graph-admission")

    def test_evidence_outside_the_subject_is_refused(self):
        doc = self.fresh()
        edge_by_id(doc, "edge:release-graph-admission")["machine"] = ["../../etc/passwd"]
        self.assertRefused(doc, "EVIDENCE_PATH_MISSING:edge:release-graph-admission")

    def test_map_cannot_evidence_itself(self):
        doc = self.fresh()
        edge_by_id(doc, "edge:release-graph-admission")["falsifier_tests"] = [retire.MAP_RELPATH]
        self.assertRefused(doc, "SELF_EVIDENCE:edge:release-graph-admission")

    def test_llm_mechanism_cannot_advance(self):
        doc = self.fresh()
        edge = edge_by_id(doc, "edge:semantic-unknown-frontier")
        edge["retirement_state"] = "FORMALIZATION_CANDIDATE"
        edge["prior_art"] = ["x"]
        edge["admitted_domain"] = "x"
        self.assertRefused(doc, "LLM_MECHANISM_CLOSED:edge:semantic-unknown-frontier")
        self.assertRefused(doc, "TERMINAL_RESIDUAL_ADVANCED:edge:semantic-unknown-frontier")

    def test_known_class_routed_to_llm_is_refused(self):
        doc = self.fresh()
        doc["mechanisms"]["repeated-generation"] = "LLM"
        self.assertRefused(doc, "MAP_INVALID:known residue classes route to LLM")

    def test_mechanism_must_match_residue_class(self):
        doc = self.fresh()
        edge_by_id(doc, "edge:handwritten-product-surface")["mechanism"] = "LLM"
        self.assertRefused(doc, "MAP_INVALID:edge:handwritten-product-surface mechanism must be ggen")

    def test_scores_are_bounded_integers(self):
        for bad in (0, 6, 2.5, True, "5"):
            doc = self.fresh()
            edge_by_id(doc, "edge:pr-ci-stewardship")["frequency"] = bad
            self.assertRefused(doc, "MAP_INVALID:edge:pr-ci-stewardship frequency")

    def test_reordered_ladder_is_refused(self):
        doc = self.fresh()
        doc["ladder"]["states"] = list(reversed(doc["ladder"]["states"]))
        self.assertRefused(doc, "MAP_INVALID:ladder.states")

    def test_duplicate_edge_is_refused(self):
        doc = self.fresh()
        doc["edge"].append(copy.deepcopy(doc["edge"][0]))
        self.assertRefused(doc, "MAP_INVALID:duplicate edge id")

    def test_dropped_terminal_refusal_is_refused(self):
        doc = self.fresh()
        doc["refusals"]["terminal"].remove("EDGE_DELETED")
        self.assertRefused(doc, "MAP_INVALID:missing terminal refusals: EDGE_DELETED")

    # -- frontier selection ------------------------------------------------

    def test_frontier_is_deterministic_argmax(self):
        picks = retire.frontier(self.doc, 100)
        scores = [pick["score"] for pick in picks]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(picks, retire.frontier(copy.deepcopy(self.doc), 100))
        self.assertEqual(picks[0]["id"], "edge:session-work-selection")

    def test_frontier_ties_break_by_id(self):
        doc = self.fresh()
        for edge in doc["edge"]:
            for field in retire.SCORE_FIELDS:
                edge[field] = 3
        ids = [pick["id"] for pick in retire.frontier(doc, 100)]
        self.assertEqual(ids, sorted(ids))

    def test_frontier_excludes_residual_blocked_and_closed(self):
        doc = self.fresh()
        edge_by_id(doc, "edge:pr-ci-stewardship")["blocked"] = "needs OCEL log export"
        closed = edge_by_id(doc, "edge:test-adequacy-judgment")
        closed["retirement_state"] = "MACHINE_VERIFIED"
        ids = {pick["id"] for pick in retire.frontier(doc, 100)}
        self.assertNotIn("edge:semantic-unknown-frontier", ids)
        self.assertNotIn("edge:pr-ci-stewardship", ids)
        self.assertNotIn("edge:test-adequacy-judgment", ids)

    def test_frontier_carries_score_basis(self):
        self.assertTrue(all(pick["score_basis"] == "ESTIMATED" for pick in retire.frontier(self.doc, 3)))

    # -- ratchet and IRR ----------------------------------------------------

    def test_deleted_edge_is_refused(self):
        after = self.fresh()
        after["edge"] = [e for e in after["edge"] if e["id"] != "edge:pr-ci-stewardship"]
        errors, _ = retire.compare(self.doc, after)
        self.assertIn(
            "EDGE_DELETED:edge:pr-ci-stewardship (residue is retired on the ladder, never deleted)",
            errors,
        )

    def test_unexplained_regression_is_refused(self):
        after = self.fresh()
        edge_by_id(after, "edge:release-graph-admission")["retirement_state"] = "LLM_ONLY"
        errors, _ = retire.compare(self.doc, after)
        self.assertTrue(any(e.startswith("LADDER_REGRESSION:edge:release-graph-admission") for e in errors))

    def test_explained_regression_is_admitted(self):
        after = self.fresh()
        edge = edge_by_id(after, "edge:release-graph-admission")
        edge["retirement_state"] = "LLM_ONLY"
        edge["regression_reason"] = "falsifier found admitted cycle"
        errors, _ = retire.compare(self.doc, after)
        self.assertEqual(errors, [])

    def test_discovery_raises_residue_without_refusal(self):
        after = self.fresh()
        new = copy.deepcopy(edge_by_id(after, "edge:pr-ci-stewardship"))
        new["id"] = "edge:pr-ci-lockfile-drift"
        after["edge"].append(new)
        errors, report = retire.compare(self.doc, after)
        self.assertEqual(errors, [])
        self.assertEqual(report["discovered_edges"], ["edge:pr-ci-lockfile-drift"])
        self.assertEqual(report["delta_llm_residue"], 1)

    def test_irr_counts_closed_edges_per_day(self):
        after = self.fresh()
        after["observed_at"] = "2026-09-27"
        edge = edge_by_id(after, "edge:test-adequacy-judgment")
        edge["retirement_state"] = "MACHINE_VERIFIED"
        errors, report = retire.compare(self.doc, after)
        self.assertEqual(errors, [])
        self.assertEqual(report["delta_closed"], 1)
        self.assertEqual(report["days"], 2)
        self.assertEqual(report["irr_per_day"], 0.5)
        self.assertEqual(report["advanced_edges"], ["edge:test-adequacy-judgment"])

    # -- CLI ----------------------------------------------------------------

    def test_cli_refuses_invalid_map(self):
        doc_text = (ROOT / retire.MAP_RELPATH).read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "map.toml"
            bad.write_text(
                doc_text.replace('retirement_state = "UNKNOWN"', 'retirement_state = "ALIVE"'),
                encoding="utf-8",
            )
            out = io.StringIO()
            with redirect_stdout(out):
                code = retire.main(["--map", str(bad)])
        self.assertEqual(code, 2)
        self.assertIn("REFUSED:MAP_INVALID:edge:ce23-machinery-absent-courts retirement_state 'ALIVE'", out.getvalue())

    def test_cli_unresolvable_baseline_is_refused(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = retire.main(["--baseline-ref", "refs/does/not/exist"])
        self.assertEqual(code, 2)
        self.assertIn("REFUSED:BASELINE_UNRESOLVED", out.getvalue())

    def test_cli_reports_frontier(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = retire.main(["--frontier", "2"])
        self.assertEqual(code, 0)
        self.assertIn('"llm_residue"', out.getvalue())
        self.assertIn("edge:session-work-selection", out.getvalue())

    def test_cli_runs_as_script(self):
        result = subprocess.run(
            ["python3", str(SCRIPT)], capture_output=True, text=True, check=False, cwd=ROOT
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
