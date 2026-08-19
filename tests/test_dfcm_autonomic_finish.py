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


def component(cid, standing, deps=(), blocker=None, receipt=False):
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
    if receipt:
        row["execution_receipt"] = f"test:{cid}"
        row["executed_sha"] = row["sha"]
    return row


def manifest(*rows, standing="UNKNOWN", required_roles=()):
    return {
        "release": {"standing": standing, "required_roles": list(required_roles)},
        "components": list(rows),
    }


class DfcmAutonomicFinishTests(unittest.TestCase):
    def test_selects_maximum_transitive_relief(self):
        subject = manifest(
            component("a", "PARTIAL_ALIVE"),
            component("b", "UNKNOWN", ["a"]),
            component("c", "ALIVE", receipt=True),
            component("d", "BUILD_BROKEN", ["c"]),
        )
        picked = dfcm.select(subject, limit=1)
        self.assertEqual(picked[0]["subject"]["component"], "a")
        self.assertEqual(picked[0]["dfcm"]["transitive_unlocks"], 1)
        self.assertFalse(picked[0]["authority"]["do"])

    def test_frontier_refuses_blocked_dependency(self):
        subject = manifest(component("a", "UNKNOWN"), component("b", "UNKNOWN", ["a"]))
        self.assertEqual([c.component_id for c in dfcm.frontier(subject)], ["a"])

    def test_exact_grant_required_for_do(self):
        subject = manifest(component("a", "UNKNOWN"))
        intent = dfcm.select(subject)[0]
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
        subject = manifest(component("a", "UNKNOWN"))
        intent = dfcm.select(subject)[0]
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
        subject = manifest(component("a", "UNKNOWN"))
        out = dfcm.cycle(subject)
        self.assertTrue(out["replay"].startswith("ALIVE:REPLAY:3:"))
        bad = copy.deepcopy(out["receipts"])
        bad[2]["event"]["phase"] = "DO"
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.replay_receipts(bad)
        self.assertEqual(caught.exception.code, "RECEIPT_TAMPERED")

    def test_cycle_is_deterministic(self):
        subject = manifest(component("a", "UNKNOWN"), component("b", "UNKNOWN", ["a"]))
        self.assertEqual(dfcm.cycle(subject), dfcm.cycle(copy.deepcopy(subject)))

    def test_cycle_refused_for_unadmitted_dependency(self):
        subject = manifest(component("a", "UNKNOWN", ["missing"]))
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.cycle(subject)
        self.assertEqual(caught.exception.code, "DEPENDENCY_NOT_ADMITTED")

    def test_definition_of_done_requires_receipt_for_alive(self):
        subject = manifest(component("a", "ALIVE"), required_roles=("a",))
        report = dfcm.definition_of_done(subject)
        self.assertFalse(report["done"])
        self.assertIn("DOD_EXECUTION_RECEIPT_MISSING", {f["code"] for f in report["findings"]})

    def test_definition_of_done_requires_exact_executed_subject(self):
        row = component("a", "ALIVE", receipt=True)
        row["executed_sha"] = "b" * 40
        report = dfcm.definition_of_done(manifest(row, required_roles=("a",)))
        self.assertFalse(report["done"])
        self.assertIn("DOD_EXECUTED_SUBJECT_DRIFT", {f["code"] for f in report["findings"]})

    def test_definition_of_done_is_computed_and_promotion_ready(self):
        subject = manifest(
            component("a", "ALIVE", receipt=True),
            component("b", "ALIVE", ["a"], receipt=True),
            required_roles=("a", "b"),
        )
        report = dfcm.definition_of_done(subject)
        self.assertTrue(report["done"])
        self.assertTrue(report["promotion_ready"])
        self.assertEqual(report["findings"], [])

    def test_release_alive_overclaim_is_refused_by_dod(self):
        subject = manifest(component("a", "UNKNOWN"), standing="ALIVE", required_roles=("a",))
        report = dfcm.definition_of_done(subject)
        self.assertFalse(report["done"])
        self.assertIn("DOD_RELEASE_STANDING_OVERCLAIM", {f["code"] for f in report["findings"]})

    def test_cycle_terminates_only_when_dod_is_true(self):
        subject = manifest(component("a", "ALIVE", receipt=True), required_roles=("a",))
        out = dfcm.cycle(subject)
        self.assertEqual(out["standing"], "ALIVE")
        self.assertEqual(out["termination"], "DONE")
        self.assertEqual(out["intents"], [])
        self.assertTrue(out["definition_of_done"]["done"])

    def test_incomplete_cycle_is_partial_and_continues(self):
        out = dfcm.cycle(manifest(component("a", "UNKNOWN")))
        self.assertEqual(out["standing"], "PARTIAL_ALIVE")
        self.assertEqual(out["termination"], "CONTINUE")
        self.assertEqual(len(out["intents"]), 1)

    def test_incomplete_without_lawful_frontier_refuses(self):
        subject = manifest(component("a", "UNSUPPORTED"), required_roles=("a",))
        with self.assertRaises(dfcm.Refusal) as caught:
            dfcm.cycle(subject)
        self.assertEqual(caught.exception.code, "NO_LAWFUL_FRONTIER")


if __name__ == "__main__":
    unittest.main()
