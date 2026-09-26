"""Anti-fabrication lock: the committed autonomic receipt recomputes byte for byte.

Expected first standing (RFC-0005 §15): execution ALIVE, autonomy NOT_AUTONOMIC, authority
WAITING_EXTERNAL_AUTHORITY, with exactly the BLOCKED gate set below. A PASS that the court
does not recompute cannot be committed.
"""

from __future__ import annotations

import copy
import unittest

from _autonomic_support import RECEIPT, RELEASE, committed_evaluation, committed_inputs, load

from scripts.release_train.autonomic_crown import receipt as receipt_mod
from scripts.release_train.autonomic_crown.__main__ import observed_time
from scripts.release_train.autonomic_crown.model import digest, pretty

EXPECTED_BLOCKED = [
    "U-01", "U-02", "U-03", "U-04", "U-08", "U-09", "U-10", "U-11",
    "U-13", "U-14", "U-15", "U-16", "U-17", "U-18",
]  # fmt: skip
EXPECTED_PASS = ["U-05", "U-06", "U-07", "U-12"]


class CommittedTest(unittest.TestCase):
    def setUp(self):
        self.committed = load(RECEIPT)

    def test_receipt_recomputes_byte_for_byte(self):
        inputs = committed_inputs(self)
        ev = committed_evaluation(self, self_attack=True)
        body = receipt_mod.build(ev, RELEASE, digest(inputs.edges_doc), digest(inputs.gates_doc), None)
        sealed = receipt_mod.seal(body, observed_time(inputs))
        self.assertEqual(pretty(sealed), RECEIPT.read_bytes())

    def test_expected_first_standing(self):
        r = self.committed
        self.assertTrue(receipt_mod.verify(r))
        self.assertEqual(r["standings"]["execution"], {"state": "ALIVE"})
        self.assertEqual(r["standings"]["autonomy"], "NOT_AUTONOMIC")
        self.assertEqual(r["standings"]["authority"]["state"], "WAITING_EXTERNAL_AUTHORITY")
        self.assertEqual(r["blocked_gates"], EXPECTED_BLOCKED)
        self.assertEqual(r["passed_gates"], EXPECTED_PASS)
        self.assertEqual(r["exit"], 3)
        self.assertEqual(r["crown_subject"], "68bacd8dcc9ae12e4e97727a284c14abdc7520c5")
        for gid in EXPECTED_BLOCKED:
            g = r["gates"][gid]
            self.assertIsNone(g["evidence"], gid)
            self.assertIn(
                g["failure_class"],
                (
                    "CAPABILITY_GAP",
                    "EVIDENCE_FAILURE",
                    "AUTHORITY_FAILURE",
                    "DEPENDENCY_FAILURE",
                    "VERIFICATION_FAILURE",
                ),
            )
            self.assertTrue(g["broken_term"])
        for gid in EXPECTED_PASS:
            self.assertRegex(r["gates"][gid]["evidence"]["digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertFalse([f for f in r["findings"] if f["severity"] == "REFUSED"])

    def test_pass_evidence_digests_match_the_recorded_reports(self):
        r = self.committed
        self.assertEqual(r["gates"]["U-07"]["evidence"]["digest"], digest(r["reports"]["mutants"]))
        self.assertEqual(r["gates"]["U-12"]["evidence"]["digest"], digest(r["reports"]["premise_set"]))
        rows = r["reports"]["self_attack"]["faults"]
        self.assertEqual(
            r["gates"]["U-05"]["evidence"]["digest"],
            digest({k: v for k, v in rows.items() if v["recoverability"] == "R"}),
        )

    def test_fabricated_pass_breaks_the_seal(self):
        forged = copy.deepcopy(self.committed)
        forged["gates"]["U-18"]["state"] = "PASS"
        self.assertFalse(receipt_mod.verify(forged))
        forged["standings"]["autonomy"] = "AUTONOMIC"
        forged["receipt_digest"] = digest({k: v for k, v in forged.items() if k != "receipt_digest"})
        self.assertTrue(receipt_mod.verify(forged))  # the seal alone is not the court...
        self.assertNotEqual(pretty(forged), RECEIPT.read_bytes())  # ...the byte-recompute lock is


if __name__ == "__main__":
    unittest.main()
