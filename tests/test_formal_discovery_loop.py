import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_formal_discovery_loop.py"
SPEC = importlib.util.spec_from_file_location("verify_formal_discovery_loop", SCRIPT)
loop = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(loop)


class FormalDiscoveryLoopTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = loop.load_toml(ROOT / "catalog" / "formal-discovery-loop.toml")

    def complete_receipt(self):
        stage_standing = {stage["id"]: "ALIVE" for stage in self.manifest["stage"]}
        return {
            "exact_subject": "subject:test-frontier-math@" + "0" * 40,
            "ontology_digest": "b3:ontology",
            "search_plan_digest": "b3:plan",
            "candidate_digest": "b3:candidate",
            "lean_toolchain": "leanprover/lean4:test",
            "lake_manifest_digest": "b3:lake-manifest",
            "axiom_audit_digest": "b3:axioms",
            "negative_control_receipts": ["receipt:negative-control"],
            "manufacturer_identities": ["repository:ggen@test"],
            "verifier_identities": ["lean:test", "lake:test", "mfact:test"],
            "replay_references": ["replay:test"],
            "admitted_delta_digest": "b3:ontology-delta",
            "standing": "ALIVE",
            "stage_standing": stage_standing,
            "violations": [],
        }

    def test_canonical_manifest_is_valid(self):
        self.assertEqual(loop.validate_manifest(self.manifest), [])

    def test_complete_receipt_reaches_alive(self):
        self.assertEqual(loop.evaluate_receipt(self.manifest, self.complete_receipt()), "ALIVE")

    def test_missing_lean_admission_is_partial_alive(self):
        receipt = self.complete_receipt()
        receipt["stage_standing"]["lean-admission"] = "UNKNOWN"
        self.assertEqual(loop.evaluate_receipt(self.manifest, receipt), "PARTIAL_ALIVE")

    def test_unreceipted_ontology_mutation_refuses(self):
        receipt = self.complete_receipt()
        receipt["violations"] = ["UNRECEIPTED_ONTOLOGY_MUTATION"]
        self.assertEqual(
            loop.evaluate_receipt(self.manifest, receipt),
            "REFUSED:UNRECEIPTED_ONTOLOGY_MUTATION",
        )

    def test_llm_authority_refuses(self):
        receipt = self.complete_receipt()
        receipt["violations"] = ["LLM_GRANTED_DO_AUTHORITY"]
        self.assertEqual(
            loop.evaluate_receipt(self.manifest, receipt),
            "REFUSED:LLM_GRANTED_DO_AUTHORITY",
        )

    def test_known_route_cannot_be_llm(self):
        manifest = copy.deepcopy(self.manifest)
        algebra = next(route for route in manifest["route"] if route["problem_class"] == "algebra")
        algebra["machine"] = "LLM"
        algebra["llm_allowed"] = True
        errors = loop.validate_manifest(manifest)
        self.assertTrue(any("route algebra must use CAS" in error for error in errors))
        self.assertTrue(any("known route algebra must not require an LLM" in error for error in errors))

    def test_semantic_unknown_must_remain_candidate_only(self):
        manifest = copy.deepcopy(self.manifest)
        unknown = next(route for route in manifest["route"] if route["problem_class"] == "semantic-unknown")
        unknown["candidate_only"] = False
        errors = loop.validate_manifest(manifest)
        self.assertIn("semantic-unknown LLM route must be candidate_only", errors)

    def test_ontology_feedback_cannot_bypass_certification(self):
        manifest = copy.deepcopy(self.manifest)
        close = next(stage for stage in manifest["stage"] if stage["id"] == "close-ontology-loop")
        close["requires"] = ["audit-axioms-and-falsifiers"]
        errors = loop.validate_manifest(manifest)
        self.assertIn("ontology feedback must depend on formal certification", errors)

    def test_stage_dependency_cycle_refuses_manifest(self):
        manifest = copy.deepcopy(self.manifest)
        reconstruct = next(stage for stage in manifest["stage"] if stage["id"] == "reconstruct-ontology")
        reconstruct["requires"] = ["close-ontology-loop"]
        errors = loop.validate_manifest(manifest)
        self.assertIn("stage dependency graph must be acyclic; recurrence is via feedback_target", errors)


if __name__ == "__main__":
    unittest.main()
