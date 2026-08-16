from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
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

    def test_marketplace_exact_subject_with_owning_receipt_is_held(self) -> None:
        packet = self.by_repo["seanchatmangpt/ggen-marketplace"]
        self.assertEqual("ALIVE", packet["standing"])
        self.assertEqual("ceb2b69ad1dc1bf0906a1979a9e18c53245181f3", packet["sha"])
        self.assertEqual(packet["sha"], packet["executed_sha"])
        self.assertEqual("github-actions:31923773826", packet["execution_receipt"])
        self.assertEqual("HOLD_EXACT_IDENTITY", packet["action"])
        self.assertIsNone(packet["branch"])

    def test_affidavit_exact_subject_with_owning_receipt_is_held(self) -> None:
        packet = self.by_repo["seanchatmangpt/affidavit"]
        self.assertEqual("ALIVE", packet["standing"])
        self.assertEqual("5dc78f113e60ba95a4b4594a6da3511334e86024", packet["sha"])
        self.assertEqual(packet["sha"], packet["executed_sha"])
        self.assertEqual("github-actions:31674647112", packet["execution_receipt"])
        self.assertEqual("HOLD_EXACT_IDENTITY", packet["action"])
        self.assertIsNone(packet["branch"])

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
        self.assertNotIn("affidavit", packet["blocked_by"])
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


class ValidatePlanFindingTests(unittest.TestCase):
    """The real plan validates clean; these prove validate_plan actually detects
    each violation type instead of always returning an empty list."""

    def setUp(self) -> None:
        manifest = plan_completion.load(ROOT / "release" / "v26.9.1" / "manifest.toml")
        policy = plan_completion.load(ROOT / "release" / "v26.9.1" / "fleet-policy.toml")
        bootstrap = plan_completion.load(ROOT / "release" / "v26.9.1" / "fanout-bootstrap.toml")
        self.plan = plan_completion.construct_plan(manifest, policy, bootstrap)

    def _packet(self, repository: str) -> dict:
        for packet in self.plan["packets"]:
            if packet["repository"] == repository:
                return packet
        raise KeyError(repository)

    def test_detects_ambient_do_authority(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["packets"][0]["do_authority"] = True
        findings = plan_completion.validate_plan(plan)
        self.assertIn(f"AMBIENT_DO_AUTHORITY:{plan['packets'][0]['repository']}", findings)

    def test_detects_invalid_sha(self) -> None:
        plan = copy.deepcopy(self.plan)
        target = next(p for p in plan["packets"] if p.get("sha"))
        target["sha"] = "not-a-real-sha"
        findings = plan_completion.validate_plan(plan)
        self.assertIn(f"INVALID_SHA:{target['repository']}:not-a-real-sha", findings)

    def test_detects_alive_without_receipt(self) -> None:
        plan = copy.deepcopy(self.plan)
        target = next(p for p in plan["packets"] if p["standing"] == "ALIVE")
        target["execution_receipt"] = ""
        findings = plan_completion.validate_plan(plan)
        self.assertIn(f"ALIVE_WITHOUT_RECEIPT:{target['repository']}", findings)

    def test_detects_build_broken_without_evidence(self) -> None:
        plan = copy.deepcopy(self.plan)
        target = next(p for p in plan["packets"] if p["standing"] == "BUILD_BROKEN")
        target["blocker"] = ""
        findings = plan_completion.validate_plan(plan)
        self.assertIn(f"BUILD_BROKEN_WITHOUT_EVIDENCE:{target['repository']}", findings)

    def test_detects_build_broken_subject_drift(self) -> None:
        plan = copy.deepcopy(self.plan)
        target = next(p for p in plan["packets"] if p["standing"] == "BUILD_BROKEN")
        target["executed_sha"] = "f" * 40
        findings = plan_completion.validate_plan(plan)
        self.assertIn(f"BUILD_BROKEN_SUBJECT_DRIFT:{target['repository']}", findings)

    def test_detects_duplicate_packet(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["packets"].append(copy.deepcopy(plan["packets"][0]))
        findings = plan_completion.validate_plan(plan)
        dupe = plan["packets"][0]
        self.assertIn(f"DUPLICATE_PACKET:{dupe['repository']}:{dupe['id']}", findings)


class MainCliTests(unittest.TestCase):
    """Exercises the argparse/main() entrypoint, which construct_plan-level unit
    tests never invoke."""

    def test_main_prints_valid_plan_json_and_exits_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "plan_completion.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("ALIVE", payload["standing"])
        self.assertEqual([], payload["findings"])

    def test_main_release_only_excludes_portfolio_packets(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "plan_completion.py"), "--release-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(0, payload["counts"]["portfolio_active"])


if __name__ == "__main__":
    unittest.main()
