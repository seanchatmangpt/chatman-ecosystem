"""Falsifier suite for ALOOP-CROWN-001 (RFC-0005 section 10, requirement R026).

Each test names the RFC-0005 law or requirement it guards. The admit path and every
refusal path are exercised; a suite with zero negative cases would itself violate F-R026.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("aloop_crown", ROOT / "scripts" / "aloop_crown.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40
SHA_D = "d" * 40
OCEL_OK = {
    "object_types": ["Episode", "WorkOrder", "Authority", "Receipt", "Worker", "Evidence"],
    "event_classes": [
        "episode.start",
        "execution.start",
        "receipt.persist",
        "verify",
        "workorder.issue",
    ],
    "event_count": 12,
}
RECEIPT_ALPHA = {
    "work_order_id": "WO-001",
    "provider": "alpha",
    "provider_execution_id": "alpha-run-7",
    "origin_authority": "operator-dispatch-001",
    "exit_status": "success",
    "replay_binding": "verifier:tests/test_aloop_crown.py",
    "consequence": "commit SHA_B on feat/loop",
}
RECEIPT_BETA = dict(RECEIPT_ALPHA, work_order_id="WO-002", provider="beta",
                    provider_execution_id="beta-run-3")


def base_record(lane: str, standing: str = "AUTONOMOUS") -> dict:
    return {
        "schema_version": "1.0.0",
        "episode": "ALOOP-ZCODE-DOGFOOD-001",
        "lane": lane,
        "author": lane,
        "objective": "demonstrate closed-loop qualification",
        "standing": standing,
        "repos": [
            {
                "repo": "chatman-ecosystem",
                "branch": "feat/aloop-loop",
                "start_sha": SHA_A,
                "final_sha": SHA_B,
                "commits": [SHA_B],
            }
        ],
        "commands": [{"cmd": "python3 -m unittest", "exit": 0}],
        "tests": [{"cmd": "python3 -m unittest tests.test_aloop_crown", "exit": 0}],
        "falsifiers": [{"id": "R005-F", "result": "PASS"}],
        "receipts": [],
        "human_causal_edges": [],
        "recurrence": {
            "demonstrated": True,
            "chain": ["Receipt[n]", "Reobserve[n+1]", "Frontier[n+1]", "WorkOrder[n+1]"],
            "iterations": 2,
        },
        "recovery": [],
        "stress": {"kind": "benchmark", "result": "PASS"},
        "ocel_summary": copy.deepcopy(OCEL_OK),
        "blockers": [],
        "authority": {"origin": "operator-dispatch-001", "ceiling": "no-deploy", "violations": []},
        "ts": "2026-09-25T18:00:00Z",
    }


def alive_lane_one() -> dict:
    record = base_record("lane-1", "AUTONOMOUS")
    record["receipts"] = [copy.deepcopy(RECEIPT_ALPHA)]
    return record


def alive_lane_two() -> dict:
    record = base_record("lane-2", "AUTONOMOUS")
    record["repos"][0] = {
        "repo": "engineering-standards",
        "branch": "docs/aloop-rfc",
        "start_sha": SHA_C,
        "final_sha": SHA_D,
        "commits": [],
    }
    record["receipts"] = [copy.deepcopy(RECEIPT_BETA)]
    record["recovery"] = [{"from": "execution.crash", "via": "replan", "to": "success",
                           "human_edges": 0}]
    return record


def write_corpus(records: dict) -> Path:
    tmp = tempfile.mkdtemp(prefix="aloop-crown-test-")
    root = Path(tmp)
    for lane, record in records.items():
        lane_dir = root / lane
        lane_dir.mkdir()
        if record is not None:
            (lane_dir / "record.json").write_text(json.dumps(record), encoding="utf-8")
    return root


class AutonomousLoopCrownTests(unittest.TestCase):
    def test_alive_corpus_admits(self):
        """R020: the conjunction admits exactly when every term passes."""
        root = write_corpus({"lane-1": alive_lane_one(), "lane-2": alive_lane_two()})
        result = mod.verdict(mod.load_lane_records(root), "ALOOP-ZCODE-DOGFOOD-001", root)
        self.assertEqual("AUTONOMOUS_LOOP_ALIVE", result["standing"])
        self.assertEqual([], result["missing_terms"])
        self.assertEqual([], result["violations"])

    def test_missing_lane_record_fails_terms(self):
        """R022: absent lane evidence fails terms; it is never assumed (fail-closed)."""
        root = write_corpus({"lane-1": alive_lane_one(), "lane-2": None})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertEqual("AUTONOMOUS_LOOP_PARTIAL_ALIVE", result["standing"])
        self.assertIn("LOOP", result["missing_terms"])
        self.assertTrue(any("lane-2: record.json absent" in m for m in result["terms"]["LOOP"]["missing"]))

    def test_human_causal_edge_caps_at_assisted(self):
        """R002/L1/L6: post-epoch human causality over an AUTONOMOUS claim is a violation."""
        record = alive_lane_one()
        record["human_causal_edges"] = [
            {"ts": "2026-09-25T18:05:00Z", "phase": "post-epoch-execution",
             "description": "operator redirected lane"}
        ]
        root = write_corpus({"lane-1": record})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertEqual("AUTONOMOUS_LOOP_PARTIAL_ALIVE", result["standing"])
        self.assertIn("CAUSALITY", result["missing_terms"])
        self.assertTrue(result["violations"])

    def test_no_human_input_without_recurrence_not_autonomous(self):
        """L5: silence plus no recurrence is not autonomy."""
        record = alive_lane_one()
        record["recurrence"] = {"demonstrated": False, "chain": [], "iterations": 0}
        root = write_corpus({"lane-1": record})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertIn("CAUSALITY", result["missing_terms"])
        self.assertTrue(any("law L5" in v for v in result["violations"]))

    def test_assisted_never_promoted(self):
        """L1: tainted recurrence is automation; an ASSISTED corpus never yields ALIVE."""
        record = alive_lane_one()
        record["standing"] = "ASSISTED"
        record["human_causal_edges"] = [
            {"ts": "2026-09-25T18:05:00Z", "phase": "post-epoch-execution",
             "description": "human picked next work order"}
        ]
        root = write_corpus({"lane-1": record})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertNotEqual("AUTONOMOUS_LOOP_ALIVE", result["standing"])
        self.assertIn("LOOP", result["missing_terms"])

    def test_provider_identity_in_work_order_refused(self):
        """R006/R025: provider token in work_order_id is REFUSED, never scored."""
        record = alive_lane_one()
        record["receipts"][0]["work_order_id"] = "WO-alpha-provider-locked"
        root = write_corpus({"lane-1": record})
        with self.assertRaises(mod.Refusal) as caught:
            mod.load_lane_records(root)
            mod.evaluate({"lane-1": mod.load_lane_records(root)["lane-1"]})
        self.assertEqual("PROVIDER_NEUTRALITY", caught.exception.code)

    def test_single_provider_without_replace_fails(self):
        """L2: worker-level reissuance proves nothing about provider lock-in."""
        lane1 = alive_lane_one()
        lane2 = alive_lane_two()
        lane2["receipts"] = [dict(RECEIPT_BETA, provider="alpha")]
        root = write_corpus({"lane-1": lane1, "lane-2": lane2})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertIn("PROVIDERS", result["missing_terms"])
        self.assertTrue(any("INSUFFICIENT_PROVIDER_DIVERSITY" in m
                            for m in result["terms"]["PROVIDERS"]["missing"]))

    def test_recovery_and_stress_absent_fail(self):
        """R009/R011: NOT_RUN is honest and fails terms requiring it; never assumed PASS."""
        lane1 = alive_lane_one()
        lane1["stress"] = {"kind": "benchmark", "result": "NOT_RUN"}
        lane2 = alive_lane_two()
        lane2["recovery"] = []
        lane2["stress"] = {"kind": "soak", "result": "NOT_RUN"}
        root = write_corpus({"lane-1": lane1, "lane-2": lane2})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertEqual(sorted(["RECOVERY", "STRESS"]), result["missing_terms"])

    def test_partial_names_missing_terms(self):
        """R024: a PARTIAL verdict names exactly which terms lacked admissible evidence."""
        root = write_corpus({"lane-1": alive_lane_one(), "lane-2": alive_lane_two()})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertEqual("AUTONOMOUS_LOOP_ALIVE", result["standing"])
        lane2 = alive_lane_two()
        lane2["recovery"] = []
        root = write_corpus({"lane-1": alive_lane_one(), "lane-2": lane2})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertEqual(["RECOVERY"], result["missing_terms"])
        self.assertEqual("AUTONOMOUS_LOOP_PARTIAL_ALIVE", result["standing"])

    def test_invalid_record_refused(self):
        """R023: malformed records are REFUSED, never partially admitted."""
        record = alive_lane_one()
        record["repos"][0]["start_sha"] = "not-a-sha"
        root = write_corpus({"lane-1": record})
        with self.assertRaises(mod.Refusal) as caught:
            mod.load_lane_records(root)
        self.assertEqual("INVALID_RECORD", caught.exception.code)

    def test_non_purpose_branch_refused(self):
        """R023/PROCESS: a lane running on main is a schema refusal."""
        record = alive_lane_one()
        record["repos"][0]["branch"] = "main"
        root = write_corpus({"lane-1": record})
        with self.assertRaises(mod.Refusal) as caught:
            mod.load_lane_records(root)
        self.assertEqual("INVALID_RECORD", caught.exception.code)

    def test_undeclared_read_only_repo_fails_process(self):
        """R008: start==final with no commits and no read_only declaration fails PROCESS."""
        record = alive_lane_one()
        record["repos"][0]["final_sha"] = SHA_A
        record["repos"][0]["commits"] = []
        root = write_corpus({"lane-1": record})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertIn("PROCESS", result["missing_terms"])
        self.assertTrue(any("read_only not declared" in m for m in result["terms"]["PROCESS"]["missing"]))

    def test_declared_read_only_repo_passes_process(self):
        """R008: an honest verification-only lane declares read_only and PROCESS admits it."""
        record = alive_lane_one()
        record["repos"][0]["final_sha"] = SHA_A
        record["repos"][0]["commits"] = []
        record["repos"][0]["read_only"] = True
        root = write_corpus({"lane-1": record})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertNotIn("PROCESS", result["missing_terms"])

    def test_empty_corpus_fails_all_terms(self):
        """Anti-vacuity: a gate with no witnessed evidence admits nothing (zero bits)."""
        root = write_corpus({"lane-1": None, "lane-2": None})
        result = mod.verdict(mod.load_lane_records(root), "E", root)
        self.assertEqual(sorted(mod.TERMS), result["missing_terms"])
        self.assertEqual("AUTONOMOUS_LOOP_PARTIAL_ALIVE", result["standing"])

    def test_no_self_certification_output_refused(self):
        """R021: the crown never writes its verdict inside the evidence root or a lane."""
        root = write_corpus({"lane-1": alive_lane_one()})
        for bad_out in (root / "verdict.json", root / "lane-1" / "verdict.json"):
            with self.assertRaises(mod.Refusal) as caught:
                mod.main(["--root", str(root), "--out", str(bad_out)])
            self.assertEqual("SELF_CERTIFICATION", caught.exception.code)


if __name__ == "__main__":
    unittest.main()
