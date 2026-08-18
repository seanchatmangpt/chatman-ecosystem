from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_crown_edges", ROOT / "scripts" / "verify_crown_edges.py"
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class CrownEdgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = mod.load(ROOT / "release" / "v26.9.1" / "crown-edges.toml")

    def evidence(self, edge_id: str, index: int = 0) -> dict[str, str]:
        digit = format((index % 15) + 1, "x")
        sha = digit * 40
        return {
            "repository": f"example/{edge_id}",
            "ref": "main",
            "sha": sha,
            "executed_sha": sha,
            "receipt": f"test:{edge_id}-{index}",
            "verifier": f"test:verifier/{edge_id}-{index}",
            "replay": f"test:replay/{edge_id}-{index}",
            "authority_class": mod.EDGE_AUTHORITY[edge_id][0],
        }

    def edge(self, candidate: dict, edge_id: str) -> dict:
        return next(edge for edge in candidate["edges"] if edge["id"] == edge_id)

    def make_all_alive(self) -> dict:
        candidate = copy.deepcopy(self.data)
        candidate["release_crown"]["standing"] = "ALIVE"
        for index, edge in enumerate(candidate["edges"]):
            edge["standing"] = "ALIVE"
            edge["evidence"] = [self.evidence(edge["id"], index)]
        return candidate

    def test_exact_mandatory_set_is_admitted_but_not_crowned(self):
        report = mod.verify(self.data)
        self.assertEqual(11, report["mandatory_edge_count"])
        self.assertEqual(11, len(report["unresolved_edges"]))
        self.assertFalse(report["release_candidate_ready"])
        self.assertFalse(report["do_authority"])
        self.assertEqual(mod.CLAIM_CEILING, report["claim_ceiling"])
        self.assertRegex(report["topology_sha256"], r"^[0-9a-f]{64}$")

    def test_topology_digest_is_deterministic(self):
        first = mod.verify(copy.deepcopy(self.data))["topology_sha256"]
        second = mod.verify(copy.deepcopy(self.data))["topology_sha256"]
        self.assertEqual(first, second)

    def test_missing_edge_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["edges"].pop()
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_EDGE_MISSING"):
            mod.verify(candidate)

    def test_unadmitted_extra_edge_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["edges"].append(
            {
                "id": "live_azure",
                "standing": "UNKNOWN",
                "allowed_authority_classes": ["DO"],
                "do_authority": False,
            }
        )
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_EDGE_UNADMITTED"):
            mod.verify(candidate)

    def test_duplicate_edge_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["edges"].append(copy.deepcopy(candidate["edges"][0]))
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_EDGE_DUPLICATE"):
            mod.verify(candidate)

    def test_schema_mismatch_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["release_crown"]["schema"] = "other/1"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_RELEASE_IDENTITY"):
            mod.verify(candidate)

    def test_unknown_root_key_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["ambient_authority"] = True
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_DOCUMENT_KEY_UNADMITTED"):
            mod.verify(candidate)

    def test_unknown_edge_key_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["edges"][0]["ambient_authority"] = "DO"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_EDGE_KEY_UNADMITTED"):
            mod.verify(candidate)

    def test_observation_requires_timezone(self):
        candidate = copy.deepcopy(self.data)
        candidate["release_crown"]["observed_at"] = "2026-08-18T06:04:40"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "OBSERVED_AT_TIMEZONE"):
            mod.verify(candidate)

    def test_claim_ceiling_cannot_expand(self):
        candidate = copy.deepcopy(self.data)
        candidate["release_crown"]["claim_ceiling"] = "RELEASE_AND_DO"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_CLAIM_CEILING"):
            mod.verify(candidate)

    def test_release_manifest_has_no_ambient_do_authority(self):
        candidate = copy.deepcopy(self.data)
        candidate["release_crown"]["do_authority"] = True
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_AMBIENT_DO_AUTHORITY"):
            mod.verify(candidate)

    def test_live_azure_cannot_be_promoted_into_crown(self):
        candidate = copy.deepcopy(self.data)
        candidate["policy"]["live_azure_mandatory"] = True
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "LIVE_AZURE_AUTHORITY_POLICY"):
            mod.verify(candidate)

    def test_live_azure_blocker_cannot_be_erased(self):
        candidate = copy.deepcopy(self.data)
        candidate["policy"]["live_azure_standing"] = "ALIVE"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "LIVE_AZURE_AUTHORITY_POLICY"):
            mod.verify(candidate)

    def test_ww3gym_cannot_escape_simulation_scope(self):
        candidate = copy.deepcopy(self.data)
        candidate["policy"]["ww3gym_scope"] = "OPERATIONAL"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "WW3GYM_SCOPE"):
            mod.verify(candidate)

    def test_bcre_is_not_brce_without_equivalence_proof(self):
        candidate = copy.deepcopy(self.data)
        candidate["policy"]["bcre_brce_equivalent"] = True
        with self.assertRaisesRegex(
            mod.CrownEdgeRefusal, "BCRE_BRCE_EQUIVALENCE_WITHOUT_PROOF"
        ):
            mod.verify(candidate)

    def test_planner_does_not_acquire_ambient_authority(self):
        candidate = copy.deepcopy(self.data)
        candidate["policy"]["planner_policy_role_agent_authority_equivalent"] = True
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "PLANNER_AUTHORITY_COLLAPSE"):
            mod.verify(candidate)

    def test_zero_unreceipted_actuation_cannot_be_disabled(self):
        candidate = copy.deepcopy(self.data)
        candidate["policy"]["zero_unreceipted_actuation"] = False
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "ZERO_UNRECEIPTED_ACTUATION_DISABLED"):
            mod.verify(candidate)

    def test_brce_remains_exclusive_do_path(self):
        candidate = copy.deepcopy(self.data)
        candidate["policy"]["brce_exclusive_do_path"] = False
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "BRCE_EXCLUSIVE_DO_PATH_DISABLED"):
            mod.verify(candidate)

    def test_authority_topology_cannot_be_expanded(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["allowed_authority_classes"] = ["SELECT", "DO"]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_EDGE_AUTHORITY_TOPOLOGY"):
            mod.verify(candidate)

    def test_edge_cannot_acquire_ambient_do_authority(self):
        candidate = copy.deepcopy(self.data)
        self.edge(candidate, "brce_consequential_boundary")["do_authority"] = True
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_EDGE_AMBIENT_DO_AUTHORITY"):
            mod.verify(candidate)

    def test_unknown_edge_cannot_carry_evidence(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["evidence"] = [self.evidence(edge["id"])]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "UNKNOWN_WITH_CLAIMS"):
            mod.verify(candidate)

    def test_partial_alive_requires_execution_evidence(self):
        candidate = copy.deepcopy(self.data)
        self.edge(candidate, "semantic_o_star")["standing"] = "PARTIAL_ALIVE"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "PARTIAL_WITHOUT_EVIDENCE"):
            mod.verify(candidate)

    def test_alive_without_evidence_is_refused(self):
        candidate = copy.deepcopy(self.data)
        self.edge(candidate, "semantic_o_star")["standing"] = "ALIVE"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "ALIVE_WITHOUT_EVIDENCE"):
            mod.verify(candidate)

    def test_alive_with_exact_execution_evidence_is_admitted_but_crown_remains_unresolved(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["standing"] = "ALIVE"
        edge["evidence"] = [self.evidence(edge["id"])]
        report = mod.verify(candidate)
        self.assertNotIn("semantic_o_star", report["unresolved_edges"])
        self.assertFalse(report["release_candidate_ready"])

    def test_executed_sha_is_mandatory(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["standing"] = "ALIVE"
        evidence = self.evidence(edge["id"])
        evidence.pop("executed_sha")
        edge["evidence"] = [evidence]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "EVIDENCE.*KEY_MISSING:executed_sha"):
            mod.verify(candidate)

    def test_execution_identity_transfer_is_refused(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["standing"] = "ALIVE"
        evidence = self.evidence(edge["id"])
        evidence["executed_sha"] = "f" * 40
        edge["evidence"] = [evidence]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "EVIDENCE_IDENTITY"):
            mod.verify(candidate)

    def test_receipt_is_mandatory_and_typed(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["standing"] = "ALIVE"
        evidence = self.evidence(edge["id"])
        evidence["receipt"] = "not a receipt"
        edge["evidence"] = [evidence]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "EVIDENCE_RECEIPT"):
            mod.verify(candidate)

    def test_verifier_is_mandatory(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["standing"] = "ALIVE"
        evidence = self.evidence(edge["id"])
        evidence.pop("verifier")
        edge["evidence"] = [evidence]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "KEY_MISSING:verifier"):
            mod.verify(candidate)

    def test_replay_is_mandatory(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["standing"] = "ALIVE"
        evidence = self.evidence(edge["id"])
        evidence.pop("replay")
        edge["evidence"] = [evidence]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "KEY_MISSING:replay"):
            mod.verify(candidate)

    def test_evidence_authority_escalation_is_refused(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["standing"] = "ALIVE"
        evidence = self.evidence(edge["id"])
        evidence["authority_class"] = "DO"
        edge["evidence"] = [evidence]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "EVIDENCE_AUTHORITY"):
            mod.verify(candidate)

    def test_duplicate_receipt_within_edge_is_refused(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["standing"] = "ALIVE"
        first = self.evidence(edge["id"], 0)
        second = self.evidence(edge["id"], 1)
        second["receipt"] = first["receipt"]
        edge["evidence"] = [first, second]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "DUPLICATE_RECEIPT"):
            mod.verify(candidate)

    def test_evidence_semantic_smuggling_is_refused(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "semantic_o_star")
        edge["standing"] = "ALIVE"
        evidence = self.evidence(edge["id"])
        evidence["do_authority"] = True
        edge["evidence"] = [evidence]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "EVIDENCE.*KEY_UNADMITTED"):
            mod.verify(candidate)

    def test_blocked_requires_reason(self):
        candidate = copy.deepcopy(self.data)
        self.edge(candidate, "gymact_domain_world_court")["standing"] = "BLOCKED"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "BLOCKED_WITHOUT_REASON"):
            mod.verify(candidate)

    def test_blocked_cannot_claim_execution(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "gymact_domain_world_court")
        edge["standing"] = "BLOCKED"
        edge["blocker"] = "EXTERNAL_RUNNER_AUTHORIZATION"
        edge["evidence"] = [self.evidence(edge["id"])]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "BLOCKED_WITH_EXECUTION"):
            mod.verify(candidate)

    def test_build_broken_requires_reason(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "bcinr_cmca_mfw_consumption")
        edge["standing"] = "BUILD_BROKEN"
        edge["evidence"] = [self.evidence(edge["id"])]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "BUILD_BROKEN_WITHOUT_REASON"):
            mod.verify(candidate)

    def test_build_broken_requires_observed_execution(self):
        candidate = copy.deepcopy(self.data)
        edge = self.edge(candidate, "bcinr_cmca_mfw_consumption")
        edge["standing"] = "BUILD_BROKEN"
        edge["blocker"] = "NON_MUTANT_BASELINE_EXIT_101"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "BUILD_BROKEN_WITHOUT_EXECUTION"):
            mod.verify(candidate)

    def test_crown_alive_with_unresolved_edges_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["release_crown"]["standing"] = "ALIVE"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_ALIVE_WITH_UNRESOLVED_EDGES"):
            mod.verify(candidate)

    def test_all_edges_alive_requires_crown_standing_to_match(self):
        candidate = self.make_all_alive()
        candidate["release_crown"]["standing"] = "UNKNOWN"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_STANDING_STALE"):
            mod.verify(candidate)

    def test_synthetic_full_closure_derives_ready_without_conferring_real_standing(self):
        candidate = self.make_all_alive()
        report = mod.verify(candidate)
        self.assertEqual([], report["unresolved_edges"])
        self.assertTrue(report["release_candidate_ready"])
        self.assertFalse(report["do_authority"])


if __name__ == "__main__":
    unittest.main()
