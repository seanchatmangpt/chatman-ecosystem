from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_crown_edges", ROOT / "scripts" / "verify_crown_edges.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class CrownEdgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = mod.load(ROOT / "release" / "v26.9.1" / "crown-edges.toml")

    def test_exact_mandatory_set_is_admitted_but_not_crowned(self):
        report = mod.verify(self.data)
        self.assertEqual(11, report["mandatory_edge_count"])
        self.assertEqual(11, len(report["unresolved_edges"]))
        self.assertFalse(report["release_candidate_ready"])
        self.assertFalse(report["do_authority"])

    def test_missing_edge_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["edges"].pop()
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_EDGE_MISSING"):
            mod.verify(candidate)

    def test_unadmitted_extra_edge_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["edges"].append({"id": "live_azure", "standing": "UNKNOWN"})
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "CROWN_EDGE_UNADMITTED"):
            mod.verify(candidate)

    def test_live_azure_cannot_be_promoted_into_crown(self):
        candidate = copy.deepcopy(self.data)
        candidate["policy"]["live_azure_mandatory"] = True
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "LIVE_AZURE_AUTHORITY_POLICY"):
            mod.verify(candidate)

    def test_bcre_is_not_brce_without_equivalence_proof(self):
        candidate = copy.deepcopy(self.data)
        candidate["policy"]["bcre_brce_equivalent"] = True
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "BCRE_BRCE_EQUIVALENCE_WITHOUT_PROOF"):
            mod.verify(candidate)

    def test_planner_does_not_acquire_ambient_authority(self):
        candidate = copy.deepcopy(self.data)
        candidate["policy"]["planner_policy_role_agent_authority_equivalent"] = True
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "PLANNER_AUTHORITY_COLLAPSE"):
            mod.verify(candidate)

    def test_alive_without_evidence_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["edges"][0]["standing"] = "ALIVE"
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "ALIVE_WITHOUT_EVIDENCE"):
            mod.verify(candidate)

    def test_execution_identity_transfer_is_refused(self):
        candidate = copy.deepcopy(self.data)
        candidate["edges"][0]["standing"] = "ALIVE"
        candidate["edges"][0]["evidence"] = [{"sha": "a" * 40, "executed_sha": "b" * 40, "receipt": "local:test"}]
        with self.assertRaisesRegex(mod.CrownEdgeRefusal, "EVIDENCE_IDENTITY"):
            mod.verify(candidate)


if __name__ == "__main__":
    unittest.main()
