from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("plan_completion", ROOT / "scripts" / "plan_completion.py")
plan_completion = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = plan_completion
SPEC.loader.exec_module(plan_completion)


class CompletionFanoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = plan_completion.load(ROOT / "release" / "v26.9.1" / "manifest.toml")
        self.policy = plan_completion.load(ROOT / "release" / "v26.9.1" / "fleet-policy.toml")
        self.bootstrap = plan_completion.load(ROOT / "release" / "v26.9.1" / "fanout-bootstrap.toml")
        self.plan = plan_completion.construct_plan(self.manifest, self.policy, self.bootstrap)
        self.by_repo = {packet["repository"]: packet for packet in self.plan["packets"]}

    def test_all_release_components_are_fanned_out_once(self) -> None:
        admitted = {component["repository"] for component in self.manifest["components"]}
        planned = [
            packet["repository"]
            for packet in self.plan["packets"]
            if packet["repository"] in admitted
        ]
        self.assertEqual(16, len(planned))
        self.assertEqual(admitted, set(planned))

    def test_exact_failure_becomes_repair_work_without_losing_receipt(self) -> None:
        packet = self.by_repo["seanchatmangpt/star-toml"]
        self.assertEqual("REPAIR_EXACT_FAILURE", packet["action"])
        self.assertEqual("BUILD_BROKEN", packet["standing"])
        self.assertEqual(packet["sha"], packet["executed_sha"])
        self.assertTrue(packet["blocker"])
        self.assertTrue(packet["execution_receipt"])

    def test_new_marketplace_subject_requires_its_own_receipt(self) -> None:
        packet = self.by_repo["seanchatmangpt/ggen-marketplace"]
        self.assertEqual("UNKNOWN", packet["standing"])
        self.assertEqual("17b716d133cf67a45d62e514cc38939283337222", packet["sha"])
        self.assertNotIn("execution_receipt", packet)
        self.assertEqual("EXECUTE_CANONICAL_VERIFIER_OR_REPAIR", packet["action"])

    def test_runtime_blockers_are_not_promoted(self) -> None:
        for repository in ("seanchatmangpt/mfw", "seanchatmangpt/gymact"):
            packet = self.by_repo[repository]
            self.assertEqual("BLOCKED", packet["standing"])
            self.assertEqual("UNBLOCK_OR_RECLASSIFY_WITH_EVIDENCE", packet["action"])
            self.assertFalse(packet["promotion_ready"])

    def test_autofde_alive_subject_is_held_not_reworked(self) -> None:
        packet = self.by_repo["seanchatmangpt/autofde"]
        self.assertEqual("ALIVE", packet["standing"])
        self.assertEqual("HOLD_EXACT_IDENTITY", packet["action"])
        self.assertIsNone(packet["branch"])

    def test_fdegym_exposes_non_alive_dependency_frontier(self) -> None:
        packet = self.by_repo["seanchatmangpt/fdegym"]
        self.assertIn("gymact", packet["blocked_by"])
        self.assertIn("mfw", packet["blocked_by"])
        self.assertIn("autofde-lab", packet["blocked_by"])
        self.assertNotIn("autofde", packet["blocked_by"])

    def test_gdmcp_is_a_typed_bootstrap_gap_not_a_substitute(self) -> None:
        packet = self.by_repo["seanchatmangpt/gdmcp"]
        self.assertEqual("BOOTSTRAP_REPOSITORY", packet["action"])
        self.assertEqual("BLOCKED", packet["standing"])
        self.assertEqual("REPOSITORY_NOT_PRESENT", packet["blocker"])
        self.assertIsNone(packet["sha"])
        self.assertNotEqual("seanchatmangpt/ggen-mcp", packet["repository"])

    def test_all_active_non_release_fleet_is_represented(self) -> None:
        expected = set()
        for key in plan_completion.ACTIVE_FLEET_KEYS:
            expected.update(self.policy["dispositions"][key])
        planned = {
            packet["repository"]
            for packet in self.plan["packets"]
            if packet["disposition"] in {"ADAPTER", "BENCH_GYM", "SOURCE_ARCHAEOLOGY"}
        }
        self.assertEqual(expected, planned)

    def test_every_packet_is_powerless(self) -> None:
        self.assertTrue(self.plan["packets"])
        self.assertTrue(all(packet["do_authority"] is False for packet in self.plan["packets"]))
        self.assertFalse(self.plan["authority"]["do"])

    def test_plan_is_deterministic(self) -> None:
        replay = plan_completion.construct_plan(self.manifest, self.policy, self.bootstrap)
        self.assertEqual(self.plan, replay)

    def test_plan_validates(self) -> None:
        self.assertEqual([], plan_completion.validate_plan(self.plan))


if __name__ == "__main__":
    unittest.main()
