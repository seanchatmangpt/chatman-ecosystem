from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("errc_portfolio", ROOT / "scripts" / "errc_portfolio.py")
errc = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = errc
SPEC.loader.exec_module(errc)


def policy() -> dict:
    return {
        "errc": {
            "schema": "test.errc.v1",
            "focus_fraction": 0.4,
            "minimum_relief_coverage": 0.8,
            "max_active_prs_per_repository": 1,
            "do_authority": False,
            "freeze_dispositions": ["OUT_OF_RELEASE"],
            "reduce_dispositions": ["ADAPTER"],
            "eliminate_pr_title_prefixes": ["merge: consolidate"],
            "reduce_pr_title_prefixes": ["docs: align"],
        }
    }


def manifest() -> dict:
    return {
        "release": {"version": "x"},
        "components": [
            {"id": "a", "repository": "o/a", "role": "root", "required": True, "standing": "UNKNOWN", "depends_on": []},
            {"id": "b", "repository": "o/b", "role": "root", "required": True, "standing": "UNKNOWN", "depends_on": []},
            {"id": "c", "repository": "o/c", "role": "leaf", "required": True, "standing": "UNKNOWN", "depends_on": ["a"]},
            {"id": "d", "repository": "o/d", "role": "leaf", "required": True, "standing": "UNKNOWN", "depends_on": ["a"]},
            {"id": "e", "repository": "o/e", "role": "crown", "required": True, "standing": "UNKNOWN", "depends_on": ["c", "b"]},
        ],
    }


def survey() -> dict:
    return {
        "observed_at": "2026-08-19T17:00:00Z",
        "owner": "o",
        "summary": {"inventory_mode": "fixture", "inventory_complete": True, "inventory_standing": "ALIVE"},
        "repositories": [
            {"repository": "o/a", "fleet_disposition": "REQUIRED"},
            {"repository": "o/b", "fleet_disposition": "REQUIRED"},
            {"repository": "o/adapter", "fleet_disposition": "ADAPTER"},
            {"repository": "o/old", "fleet_disposition": "OUT_OF_RELEASE"},
        ],
        "open_core_prs": [
            {"repository": "o/a", "number": 1, "title": "merge: consolidate relevant a"},
            {"repository": "o/a", "number": 2, "title": "feat: real implementation"},
            {"repository": "o/b", "number": 3, "title": "docs: align b with release"},
        ],
    }


class ERRCPlanTests(unittest.TestCase):
    def test_focus_prefers_dependency_ready_high_relief_roots(self) -> None:
        focus = errc.focus(manifest(), policy())
        self.assertEqual(2, focus["budget"])
        self.assertEqual(["a", "b"], [row["component"] for row in focus["selected"]])
        self.assertTrue(focus["target_met"])
        self.assertEqual(1.0, focus["coverage"])

    def test_unresolved_dependency_cannot_enter_focus(self) -> None:
        data = manifest()
        data["components"][2]["standing"] = "BUILD_BROKEN"
        focus = errc.focus(data, policy())
        selected = {row["component"] for row in focus["selected"]}
        self.assertNotIn("e", selected)

    def test_cycle_is_refused(self) -> None:
        data = manifest()
        data["components"][0]["depends_on"] = ["e"]
        with self.assertRaises(errc.ERRCError):
            errc.focus(data, policy())

    def test_actions_classify_wip_without_mutating_it(self) -> None:
        plan = errc.build(manifest(), {"fleet": {"owner": "o"}}, survey(), policy())
        eliminate = plan["actions"]["ELIMINATE"]
        reduce = plan["actions"]["REDUCE"]
        self.assertTrue(any(row["subject"] == "o/a#1" and row["physical_close"] is False for row in eliminate))
        self.assertTrue(any(row["subject"] == "o/b#3" and row["physical_close"] is False for row in reduce))
        self.assertTrue(any(row["subject"] == "o/a" and row["potential_wip_reduction"] == 1 for row in reduce))
        self.assertFalse(plan["authority"]["do_authority"])
        self.assertEqual("UNCHANGED", plan["release_standing"])

    def test_replay_is_deterministic(self) -> None:
        first = errc.build(manifest(), {"fleet": {"owner": "o"}}, survey(), policy())
        second = errc.build(manifest(), {"fleet": {"owner": "o"}}, survey(), policy())
        self.assertEqual(first["plan_digest_sha256"], second["plan_digest_sha256"])
        self.assertEqual(first, second)

    def test_do_authority_policy_is_refused(self) -> None:
        bad = copy.deepcopy(policy())
        bad["errc"]["do_authority"] = True
        with self.assertRaises(errc.ERRCError):
            errc.build(manifest(), {"fleet": {"owner": "o"}}, survey(), bad)


if __name__ == "__main__":
    unittest.main()
