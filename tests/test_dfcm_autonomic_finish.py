import copy
import importlib.util
import pathlib
import sys
import unittest

MODULE = pathlib.Path(__file__).parents[0].parent / "scripts" / "dfcm_autonomic_finish.py"
spec = importlib.util.spec_from_file_location("dfcm", MODULE)
dfcm = importlib.util.module_from_spec(spec)
assert spec.loader
sys.modules[spec.name] = dfcm
spec.loader.exec_module(dfcm)


def component(cid, standing, deps=(), blocker=None):
    row = {
        "id": cid,
        "repository": f"seanchatmangpt/{cid}",
        "ref": "main",
        "sha": (cid[0] if cid[0] in "abcdef" else "a") * 40,
        "role": cid,
        "standing": standing,
        "required": True,
        "depends_on": list(deps),
    }
    if blocker:
        row["blocker"] = blocker
    return row


class DfcmAutonomicFinishTests(unittest.TestCase):
    def test_selects_maximum_transitive_relief(self):
        manifest = {"components": [
            component("a", "PARTIAL_ALIVE"),
            component("b", "UNKNOWN", ["a"]),
            component("c", "ALIVE"),
            component("d", "BUILD_BROKEN", ["c"]),
        ]}
        picked = dfcm.select(manifest, limit=1)
        self.assertEqual(picked[0]["subject"]["component"], "a")
        self.assertEqual(picked[0]["dfcm"]["transitive_unlocks"], 1)
        self.assertFalse(picked[0]["authority"]["do"])

    def test_frontier_refuses_blocked_dependency(self):
        manifest = {"components": [component("a", "UNKNOWN"), component("b", "UNKNOWN", ["a"])]}
        self.assertEqual([c.component_id for c in dfcm.frontier(manifest)], ["a"])

    def test_exact_grant_required_for_do(self):
        manifest = {"components": [component("a", "UNKNOWN")]}
        intent = dfcm.select(manifest)[0]
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.admit_do(intent, None)
        self.assertEqual(caught.exception.code, "DO_AUTHORITY_MISSING")
        grant = {
            "subject_sha": intent["subject"]["sha"],
            "intent_digest": intent["intent_digest"],
            "scope": "BRCE:VERIFY_REPAIR_ONLY",
            "expires_at": "2026-08-20T00:00:00Z",
            "authority_id": "test-authority",
        }
        self.assertTrue(dfcm.admit_do(intent, grant)["admitted"])

    def test_grant_subject_drift_is_refused(self):
        manifest = {"components": [component("a", "UNKNOWN")]}
        intent = dfcm.select(manifest)[0]
        grant = {
            "subject_sha": "b" * 40,
            "intent_digest": intent["intent_digest"],
            "scope": "BRCE:VERIFY_REPAIR_ONLY",
            "expires_at": "2026-08-20T00:00:00Z",
            "authority_id": "test-authority",
        }
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.admit_do(intent, grant)
        self.assertEqual(caught.exception.code, "DO_SUBJECT_DRIFT")

    def test_receipt_replay_detects_tamper(self):
        manifest = {"components": [component("a", "UNKNOWN")]}
        out = dfcm.cycle(manifest)
        self.assertTrue(out["replay"].startswith("ALIVE:REPLAY:2:"))
        bad = copy.deepcopy(out["receipts"])
        bad[1]["event"]["phase"] = "DO"
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.replay_receipts(bad)
        self.assertEqual(caught.exception.code, "RECEIPT_TAMPERED")

    def test_cycle_is_deterministic(self):
        manifest = {"components": [component("a", "UNKNOWN"), component("b", "UNKNOWN", ["a"])]}
        self.assertEqual(dfcm.cycle(manifest), dfcm.cycle(copy.deepcopy(manifest)))

    def test_cycle_refused(self):
        manifest = {"components": [component("a", "UNKNOWN", ["missing"])]}
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.cycle(manifest)
        self.assertEqual(caught.exception.code, "DEPENDENCY_NOT_ADMITTED")


if __name__ == "__main__":
    unittest.main()
