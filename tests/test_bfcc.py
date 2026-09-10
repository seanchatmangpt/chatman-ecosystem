import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_bfcc.py"
SPEC = importlib.util.spec_from_file_location("verify_bfcc", SCRIPT)
bfcc = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bfcc)


class BfccManifestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = bfcc.load_toml(ROOT / "catalog" / "bfcc.toml")

    def test_canonical_catalog_is_valid(self):
        self.assertEqual(bfcc.validate_manifest(self.catalog), [])

    def test_fuller_laundering_refused_when_projection_restates_principle(self):
        catalog = copy.deepcopy(self.catalog)
        gate = next(g for g in catalog["gate"] if g["letter"] == "C")
        gate["engineering_projection"] = gate["fuller_principle"]
        errors = bfcc.validate_manifest(catalog)
        self.assertTrue(any("FULLER_LAUNDERING" in error for error in errors))

    def test_missing_gate_falsifier_is_refused(self):
        catalog = copy.deepcopy(self.catalog)
        gate = next(g for g in catalog["gate"] if g["letter"] == "A")
        gate["falsifier"] = ""
        errors = bfcc.validate_manifest(catalog)
        self.assertTrue(any("falsifier" in error for error in errors))

    def test_authority_must_deny_do(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["authority"]["bfcc_grants_do_authority"] = True
        errors = bfcc.validate_manifest(catalog)
        self.assertTrue(any("bfcc_grants_do_authority" in error for error in errors))

    def test_receipt_required_fields_must_be_non_empty(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["receipt"]["required_fields"] = []
        errors = bfcc.validate_manifest(catalog)
        self.assertTrue(any("required_fields" in error for error in errors))


class BfccReceiptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = bfcc.load_toml(ROOT / "catalog" / "bfcc.toml")

    def complete_receipt(self):
        letters = [gate["letter"] for gate in self.catalog["gate"] if gate.get("mandatory") is True]
        evidence_per_gate = {
            letter: {"subject": "subject:test", "revision": "rev-1", "note": f"evidence for {letter}"}
            for letter in letters
        }
        falsifier_per_gate = {letter: f"falsifier check for {letter} ran" for letter in letters}
        return {
            "subject": "subject:test",
            "revision": "rev-1",
            "system_boundary": "scripts/verify_bfcc.py",
            "canon_sources": ["Fuller, Design Science"],
            "projection_table": "see gates",
            "inventory_examined": ["scripts/verify_bfcc.py", "tests/test_bfcc.py"],
            "gates_evaluated": letters,
            "evidence_per_gate": evidence_per_gate,
            "falsifier_per_gate": falsifier_per_gate,
            "contradictions": [],
            "omitted_gates": [],
            "resource_vector": {"cpu_seconds": 1},
            "eta_evidence": "ratio recorded",
            "lambda_evidence": "leverage recorded",
            "sigma_evidence": "",
            "unresolved_gaps": [],
            "standing": "BFCC-ALIVE",
        }

    def test_complete_receipt_reaches_bfcc_alive(self):
        receipt = self.complete_receipt()
        self.assertEqual(bfcc.evaluate_receipt(self.catalog, receipt), "BFCC-ALIVE")

    def test_incomplete_receipt_is_bfcc_partial(self):
        receipt = self.complete_receipt()
        letter = "T"
        del receipt["evidence_per_gate"][letter]
        del receipt["falsifier_per_gate"][letter]
        receipt["standing"] = "BFCC-PARTIAL"
        self.assertEqual(bfcc.evaluate_receipt(self.catalog, receipt), "BFCC-PARTIAL")

    def test_averaged_failed_gate_refused_when_standing_claims_alive(self):
        receipt = self.complete_receipt()
        letter = "Sigma"
        del receipt["evidence_per_gate"][letter]
        del receipt["falsifier_per_gate"][letter]
        # standing still (incorrectly) claims BFCC-ALIVE despite the missing mandatory gate
        self.assertEqual(receipt["standing"], "BFCC-ALIVE")
        self.assertEqual(
            bfcc.evaluate_receipt(self.catalog, receipt),
            "REFUSED:AVERAGED_FAILED_GATE",
        )

    def test_unfalsified_synergy_claim_refused_when_sigma_evidence_empty(self):
        receipt = self.complete_receipt()
        receipt["contradictions"] = ["reviewer noted a synergy claim in the composed-behavior test"]
        receipt["sigma_evidence"] = ""
        self.assertEqual(
            bfcc.evaluate_receipt(self.catalog, receipt),
            "REFUSED:UNFALSIFIED_SYNERGY_CLAIM",
        )

    def test_missing_inventory_refused(self):
        receipt = self.complete_receipt()
        receipt["inventory_examined"] = []
        self.assertEqual(
            bfcc.evaluate_receipt(self.catalog, receipt),
            "REFUSED:MISSING_INVENTORY",
        )

    def test_standing_transferred_refused_on_subject_mismatch(self):
        receipt = self.complete_receipt()
        receipt["subject"] = "subject:different-subject"
        self.assertEqual(
            bfcc.evaluate_receipt(self.catalog, receipt),
            "REFUSED:STANDING_TRANSFERRED",
        )


if __name__ == "__main__":
    unittest.main()
