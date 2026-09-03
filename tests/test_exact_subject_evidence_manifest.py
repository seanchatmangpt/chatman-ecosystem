import copy
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).parents[1] / "scripts" / "exact_subject_evidence_manifest.py"
spec = importlib.util.spec_from_file_location("m", P)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SHA = "a" * 40
BASE = {"subject": {"repo": "acme/widget", "sha": SHA}, "observations": []}

def obs(result="PASS", **kw):
    x = {"repo": "acme/widget", "sha": SHA, "sensor": "unit", "result": result, "evidence_id": "run-1"}
    x.update(kw); return x

class ManifestTests(unittest.TestCase):
    def test_all_pass_is_bounded_partial_alive_and_replays(self):
        p = copy.deepcopy(BASE); p["observations"] = [obs()]
        out = m.manufacture(p)
        self.assertEqual(out["standing"], "PARTIAL_ALIVE")
        self.assertEqual(out["claim_ceiling"], "PARTIAL_ALIVE")
        self.assertTrue(m.verify(out))

    def test_failure_is_build_broken(self):
        p = copy.deepcopy(BASE); p["observations"] = [obs("FAIL")]
        self.assertEqual(m.manufacture(p)["standing"], "BUILD_BROKEN")

    def test_pending_cannot_false_positive(self):
        p = copy.deepcopy(BASE); p["observations"] = [obs("PASS"), obs("PENDING", sensor="ci", evidence_id="run-2")]
        self.assertEqual(m.manufacture(p)["standing"], "UNKNOWN")

    def test_empty_evidence_is_unknown(self):
        self.assertEqual(m.manufacture(copy.deepcopy(BASE))["standing"], "UNKNOWN")

    def test_foreign_sha_is_typed_refusal(self):
        p = copy.deepcopy(BASE); p["observations"] = [obs(sha="b" * 40)]
        with self.assertRaisesRegex(m.Refusal, "STALE_OR_FOREIGN_SUBJECT"):
            m.manufacture(p)

    def test_conflicting_duplicate_is_refused(self):
        p = copy.deepcopy(BASE); p["observations"] = [obs("PASS"), obs("FAIL")]
        with self.assertRaisesRegex(m.Refusal, "CONFLICTING_DUPLICATE_EVIDENCE"):
            m.manufacture(p)

    def test_tamper_breaks_receipt(self):
        p = copy.deepcopy(BASE); p["observations"] = [obs()]
        out = m.manufacture(p); out["standing"] = "ALIVE"
        with self.assertRaisesRegex(m.Refusal, "RECEIPT_MISMATCH"):
            m.verify(out)

    def test_order_is_deterministic(self):
        a = obs(sensor="z", evidence_id="2")
        b = obs(sensor="a", evidence_id="1")
        p1 = copy.deepcopy(BASE); p1["observations"] = [a,b]
        p2 = copy.deepcopy(BASE); p2["observations"] = [b,a]
        self.assertEqual(m.manufacture(p1), m.manufacture(p2))

if __name__ == "__main__": unittest.main()
