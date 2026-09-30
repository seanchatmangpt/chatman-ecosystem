import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[2]
spec = importlib.util.spec_from_file_location(
    "fleet_reconcile", ROOT / "conformance" / "qme-1" / "fleet_reconcile.py"
)
fleet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fleet)
SNAPSHOT = ROOT / "conformance" / "qme-1" / "fleet-window-v26.9.30.json"


def load():
    return json.loads(SNAPSHOT.read_text())


class FleetReconcileTests(unittest.TestCase):
    def assert_refused(self, doc, code):
        with self.assertRaises(fleet.Refusal) as cm:
            fleet.check(doc)
        self.assertEqual(cm.exception.code, code)

    def test_snapshot_is_deterministic_and_evidence_only(self):
        doc = load()
        a = fleet.check(doc)
        b = fleet.check(copy.deepcopy(doc))
        self.assertEqual(a, b)
        self.assertEqual(a["repository_count"], 65)
        self.assertEqual(a["authority"], "NONE")
        self.assertEqual(a["standing"], "PARTIAL_ALIVE")

    def test_invalid_exact_subject_refused(self):
        doc = load()
        doc["repositories"][0]["head_sha"] = "main"
        self.assert_refused(doc, "INVALID_SUBJECT")

    def test_duplicate_repository_refused(self):
        doc = load()
        doc["repositories"].append(copy.deepcopy(doc["repositories"][0]))
        doc["scan"]["unique_repositories"] += 1
        self.assert_refused(doc, "DUPLICATE_REPOSITORY")

    def test_projection_cannot_grant_authority(self):
        doc = load()
        doc["repositories"][0]["projection_authority_effect"] = "DO"
        self.assert_refused(doc, "FLEET_AUTHORITY_PROMOTION")

    def test_capability_set_member_must_be_observed(self):
        doc = load()
        doc["capability_sets"][0]["members"].append("seanchatmangpt/not-observed")
        self.assert_refused(doc, "CAPABILITY_SET_INCOMPLETE")

    def test_root_ownership_is_exact(self):
        doc = load()
        doc["canonical_subject"]["repository"] = "seanchatmangpt/graphlaw"
        self.assert_refused(doc, "ROOT_OWNERSHIP_INVALID")

    def test_observation_cannot_self_promote_to_admitted(self):
        doc = load()
        doc["repositories"][0]["evidence_kind"] = "ADMITTED"
        self.assert_refused(doc, "OBSERVATION_PROMOTION")


if __name__ == "__main__":
    unittest.main()
