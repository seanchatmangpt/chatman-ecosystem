from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tpcs_pipeline", ROOT / "scripts" / "tpcs_pipeline.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class TcpsFederationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = mod.load_config()

    def runtime_receipt(self) -> dict:
        return {
            "schema": "tcps.exact-subject.v1",
            "subject_sha": self.cfg["canonical_head"],
            "verifier_state": "ALIVE",
            "failure_count": 0,
            "verifier_sha256": "a" * 64,
        }

    def projection_receipt(self) -> dict:
        return {
            "schema": "tcps.ggen-projection.v1",
            "subject_sha": self.cfg["canonical_head"],
            "projector_sha": self.cfg["projector_sha"],
            "projection_differences": 0,
            "generated_contract_py_sha256": "b" * 64,
            "generated_contract_md_sha256": "c" * 64,
            "state": "ALIVE",
        }

    def test_contract_is_composition_only(self) -> None:
        mod.validate_config(self.cfg)
        self.assertEqual(self.cfg["role"], "composition-and-standing")
        self.assertFalse(self.cfg["implementation_code_allowed"])
        self.assertFalse(self.cfg["actuation_authority"])
        self.assertFalse(self.cfg["acceptance_mutation_authority"])
        self.assertFalse(self.cfg["wip_mutation_authority"])
        self.assertTrue(self.cfg["zero_unreceipted_actuation"])

    def test_canonical_factory_is_exact_sha_bound(self) -> None:
        self.assertEqual(self.cfg["canonical_repo"], "seanchatmangpt/tcps")
        self.assertEqual(self.cfg["canonical_pr"], 1)
        self.assertRegex(self.cfg["canonical_head"], r"^[0-9a-f]{40}$")
        self.assertRegex(self.cfg["projector_sha"], r"^[0-9a-f]{40}$")

    def test_expected_artifact_names_bind_exact_head(self) -> None:
        head = self.cfg["canonical_head"]
        self.assertEqual(self.cfg["evidence"]["runtime_artifact"], f"tcps-runtime-{head}")
        self.assertEqual(self.cfg["evidence"]["projection_artifact"], f"tcps-projection-{head}")

    def test_missing_canonical_receipts_cannot_crown_factory(self) -> None:
        report = mod.evaluate(self.cfg)
        self.assertEqual(report["state"], "PARTIAL_ALIVE")
        self.assertFalse(report["runtime_receipt_bound"])
        self.assertFalse(report["projection_receipt_bound"])

    def test_both_exact_receipts_promote_federation(self) -> None:
        report = mod.evaluate(self.cfg, self.runtime_receipt(), self.projection_receipt())
        self.assertEqual(report["state"], "ALIVE")
        self.assertTrue(report["runtime_receipt_bound"])
        self.assertTrue(report["projection_receipt_bound"])
        self.assertFalse(report["implementation_authority"])
        self.assertFalse(report["actuation_authority"])

    def test_runtime_subject_drift_is_refused(self) -> None:
        runtime = self.runtime_receipt()
        runtime["subject_sha"] = "0" * 40
        with self.assertRaises(mod.FederationRefusal) as ctx:
            mod.evaluate(self.cfg, runtime, self.projection_receipt())
        self.assertTrue(str(ctx.exception).startswith("REFUSED_TPCS_IDENTITY_DRIFT"))

    def test_projection_projector_drift_is_refused(self) -> None:
        projection = self.projection_receipt()
        projection["projector_sha"] = "0" * 40
        with self.assertRaises(mod.FederationRefusal) as ctx:
            mod.evaluate(self.cfg, self.runtime_receipt(), projection)
        self.assertTrue(str(ctx.exception).startswith("REFUSED_INVALID_TPCS_PROJECTION_RECEIPT"))

    def test_runtime_verifier_failure_is_refused(self) -> None:
        runtime = self.runtime_receipt()
        runtime["failure_count"] = 1
        with self.assertRaises(mod.FederationRefusal) as ctx:
            mod.evaluate(self.cfg, runtime, self.projection_receipt())
        self.assertTrue(str(ctx.exception).startswith("REFUSED_INVALID_TPCS_RUNTIME_RECEIPT"))

    def test_projection_difference_is_refused(self) -> None:
        projection = self.projection_receipt()
        projection["projection_differences"] = 1
        with self.assertRaises(mod.FederationRefusal) as ctx:
            mod.evaluate(self.cfg, self.runtime_receipt(), projection)
        self.assertTrue(str(ctx.exception).startswith("REFUSED_INVALID_TPCS_PROJECTION_RECEIPT"))

    def test_required_capability_closure_contains_dfcm_and_do_boundary(self) -> None:
        capabilities = set(self.cfg["capabilities"]["required"])
        for value in (
            "dfcm-pareto-frontier",
            "deterministic-heijunka",
            "jidoka-andon",
            "takt-and-littles-law",
            "durable-pre-receipt-before-do",
            "final-receipt-and-replay",
            "exact-ggen-zero-diff-projection",
        ):
            self.assertIn(value, capabilities)

    def test_federation_ontology_has_no_factory_authority(self) -> None:
        text = (ROOT / "ontology" / "tpcs.ttl").read_text(encoding="utf-8")
        self.assertIn("tpcsf:implementationAuthority false", text)
        self.assertIn("tpcsf:actuationAuthority false", text)
        self.assertIn("tpcsf:zeroUnreceiptedActuation true", text)
        self.assertIn(self.cfg["canonical_head"], text)


if __name__ == "__main__":
    unittest.main()
