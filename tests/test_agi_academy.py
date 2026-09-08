import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_agi_academy.py"
SPEC = importlib.util.spec_from_file_location("verify_agi_academy", SCRIPT)
academy = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(academy)


class AgiAcademyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = academy.load_toml(ROOT / "catalog" / "agi-academy.toml")

    def complete_receipt(self):
        modules = {
            module["id"]: "ALIVE"
            for module in self.manifest["module"]
            if module.get("mandatory") is True
        }
        return {
            "candidate_identity": "candidate:test-agi",
            "academy_release": self.manifest["release"],
            "ecosystem_sha": "0" * 40,
            "capability_set": sorted(modules),
            "verifier_identities": ["verifier:test"],
            "environment_identity": "environment:test",
            "execution_receipts": ["receipt:test"],
            "replay_references": ["replay:test"],
            "standing": "ALIVE",
            "issued_at": "2026-09-08T00:00:00Z",
            "module_standing": modules,
            "violations": [],
        }

    def test_canonical_manifest_is_valid(self):
        self.assertEqual(academy.validate_manifest(self.manifest), [])

    def test_all_mandatory_modules_alive_graduates(self):
        receipt = self.complete_receipt()
        self.assertEqual(academy.evaluate_receipt(self.manifest, receipt), "ALIVE")

    def test_missing_module_evidence_is_partial_alive(self):
        receipt = self.complete_receipt()
        receipt["module_standing"]["brce"] = "UNKNOWN"
        self.assertEqual(
            academy.evaluate_receipt(self.manifest, receipt), "PARTIAL_ALIVE"
        )

    def test_terminal_authority_violation_refuses(self):
        receipt = self.complete_receipt()
        receipt["violations"] = ["UNAUTHORIZED_DO"]
        self.assertEqual(
            academy.evaluate_receipt(self.manifest, receipt),
            "REFUSED:UNAUTHORIZED_DO",
        )

    def test_unknown_dependency_invalidates_manifest(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["module"][0]["requires"] = ["does-not-exist"]
        errors = academy.validate_manifest(manifest)
        self.assertTrue(any("unknown module" in error for error in errors))

    def test_dependency_cycle_invalidates_manifest(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["module"][0]["requires"] = ["retire-yourself-capstone"]
        errors = academy.validate_manifest(manifest)
        self.assertIn("module dependency graph must be acyclic", errors)


if __name__ == "__main__":
    unittest.main()
