import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_frontier_release_factory.py"
SPEC = importlib.util.spec_from_file_location("verify_frontier_release_factory", SCRIPT)
factory = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(factory)


class FrontierReleaseFactoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = factory.load_manifest(ROOT / "catalog" / "frontier-release-factory.toml")

    def complete_receipt(self):
        return {
            "source_identity": "release:example",
            "source_digest": "blake3:source",
            "opportunity_identity": "opportunity:example",
            "target_repository": "seanchatmangpt/example",
            "implementation_subject": "seanchatmangpt/example@" + "0" * 40,
            "verifier_identities": ["verifier:test"],
            "execution_receipts": ["receipt:test"],
            "replay_references": ["replay:test"],
            "claim_standing": {"claim:1": "ALIVE"},
            "replay_reactuated_do": False,
            "violations": [],
        }

    def test_canonical_manifest_validates(self):
        self.assertEqual(factory.validate_manifest(self.manifest), [])

    def test_complete_evidence_receipt_is_alive(self):
        self.assertEqual(factory.evaluate_receipt(self.manifest, self.complete_receipt()), "ALIVE")

    def test_source_release_as_authority_refuses(self):
        receipt = self.complete_receipt()
        receipt["violations"] = ["SOURCE_RELEASE_AS_AUTHORITY"]
        self.assertEqual(
            factory.evaluate_receipt(self.manifest, receipt),
            "REFUSED:SOURCE_RELEASE_AS_AUTHORITY",
        )

    def test_replay_must_not_reactuate_do(self):
        receipt = self.complete_receipt()
        receipt["replay_reactuated_do"] = True
        self.assertEqual(
            factory.evaluate_receipt(self.manifest, receipt),
            "REFUSED:REPLAY_REACTUATED_DO",
        )

    def test_unearned_claim_is_partial_alive(self):
        receipt = self.complete_receipt()
        receipt["claim_standing"]["claim:2"] = "PARTIAL_ALIVE"
        self.assertEqual(factory.evaluate_receipt(self.manifest, receipt), "PARTIAL_ALIVE")

    def test_llm_route_cannot_gain_authority(self):
        manifest = copy.deepcopy(self.manifest)
        llm = next(route for route in manifest["route"] if route["route"] == "LLM")
        llm["authority"] = "DO"
        self.assertTrue(any("LLM route" in error for error in factory.validate_manifest(manifest)))

    def test_repository_creation_requires_broker_and_receipt(self):
        manifest = copy.deepcopy(self.manifest)
        stage = next(stage for stage in manifest["stage"] if stage["id"] == "create-repository")
        stage["broker_required"] = False
        stage["receipt_required"] = False
        errors = factory.validate_manifest(manifest)
        self.assertTrue(any("must require broker" in error for error in errors))
        self.assertTrue(any("must require receipt" in error for error in errors))

    def test_working_backwards_release_cannot_be_earned_by_declaration(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["release_contract"]["working_backwards_status"] = "ALIVE"
        self.assertIn(
            "working-backwards release must remain CANDIDATE",
            factory.validate_manifest(manifest),
        )

    def test_missing_repository_role_invalidates_contract(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["repository_role"] = manifest["repository_role"][:-1]
        self.assertIn(
            "repository roles must be complete and unique",
            factory.validate_manifest(manifest),
        )


if __name__ == "__main__":
    unittest.main()
