"""RFC-0005 §4 orthogonal standings, AUTONOMIC => ALIVE, legality, gate admission, exit codes."""

from __future__ import annotations

import unittest

from scripts.release_train.autonomic_crown import gates, standing
from scripts.release_train.autonomic_crown.model import GATE_IDS, GateResult, digest

GOOD_GOV = {
    "main": {"protected": True},
    "environments": {"release-crown": {"reviewers": 1, "protected_branches": True}},
}


def all_pass():
    return [GateResult(g, "PASS", 0, "0", evidence={"kind": "k", "digest": digest(g)}) for g in GATE_IDS]


class StandingsTest(unittest.TestCase):
    def test_autonomic_requires_every_gate_and_alive(self):
        self.assertEqual(standing.autonomy_of(all_pass(), "ALIVE"), ("AUTONOMIC", []))
        state, found = standing.autonomy_of(all_pass(), "BLOCKED")
        self.assertEqual(state, "NOT_AUTONOMIC")
        self.assertEqual([f.code for f in found], ["AUTONOMY_WITHOUT_ALIVE"])
        one_blocked = all_pass()
        one_blocked[-1] = GateResult("U-18", "BLOCKED", "1/3", "3/3", "INSUFFICIENT_CLEAN_CYCLES")
        self.assertEqual(standing.autonomy_of(one_blocked, "ALIVE"), ("NOT_AUTONOMIC", []))
        self.assertEqual(standing.autonomy_of(all_pass()[:-1], "ALIVE")[0], "NOT_AUTONOMIC")

    def test_legal_combinations(self):
        for execution, autonomy, authority in (
            ("ALIVE", "AUTONOMIC", "AUTHORIZED"),
            ("ALIVE", "AUTONOMIC", "WAITING_EXTERNAL_AUTHORITY"),
            ("ALIVE", "NOT_AUTONOMIC", "AUTHORIZED"),
            ("ALIVE", "NOT_AUTONOMIC", "WAITING_EXTERNAL_AUTHORITY"),
            ("ALIVE", "UNKNOWN", "REFUSED"),
            ("BLOCKED", "NOT_AUTONOMIC", "WAITING_EXTERNAL_AUTHORITY"),
            ("UNKNOWN", "UNKNOWN", "AUTHORIZED"),
        ):
            with self.subTest(triple=(execution, autonomy, authority)):
                self.assertEqual(standing.legality(execution, autonomy, authority), [])

    def test_illegal_combinations_are_refused(self):
        for execution in ("PARTIAL_ALIVE", "BLOCKED", "UNSUPPORTED", "REFUSED", "UNKNOWN"):
            codes = [f.code for f in standing.legality(execution, "AUTONOMIC", "AUTHORIZED")]
            self.assertEqual(codes, ["AUTONOMY_WITHOUT_ALIVE"], execution)
        codes = [
            f.code for f in standing.legality("ALIVE", "NOT_AUTONOMIC", "REFUSED", do_receipts_without_authority=1)
        ]
        self.assertEqual(codes, ["ILLEGAL_STANDING_COMBINATION"])
        self.assertEqual(
            [f.code for f in standing.legality("ALIVE", "MOSTLY", "AUTHORIZED")], ["ILLEGAL_STANDING_COMBINATION"]
        )

    def test_authority_standing(self):
        self.assertEqual(standing.authority_of(GOOD_GOV, [])[0], "AUTHORIZED")
        self.assertEqual(standing.authority_of(None, [])[0], "WAITING_EXTERNAL_AUTHORITY")
        unprotected = {**GOOD_GOV, "main": {"protected": False}}
        self.assertEqual(standing.authority_of(unprotected, []), ("WAITING_EXTERNAL_AUTHORITY", "main unprotected"))
        no_reviewer = {**GOOD_GOV, "environments": {"release-crown": {"reviewers": 0, "protected_branches": True}}}
        self.assertIn("no required reviewer", standing.authority_of(no_reviewer, [])[1])
        from scripts.release_train.autonomic_crown.model import Finding

        self.assertEqual(standing.authority_of(GOOD_GOV, [Finding("AUTHORITY_AMPLIFICATION", "E-X")])[0], "REFUSED")

    def test_gate_pass_requires_evidence(self):
        self.assertEqual(gates.admit(all_pass()), [])
        bare = all_pass()
        bare[3] = GateResult("U-04", "PASS", "13/13", "100%")
        self.assertEqual([(f.code, f.subject) for f in gates.admit(bare)], [("GATE_PASS_WITHOUT_EVIDENCE", "U-04")])
        untyped = all_pass()
        untyped[0] = GateResult("U-01", "BLOCKED", "1/2", "100%")
        self.assertEqual([f.code for f in gates.admit(untyped)], ["GATE_COVERAGE_GAP"])
        self.assertEqual([f.subject for f in gates.admit(all_pass()[1:])], ["U-01"])

    def test_execution_standing(self):
        from scripts.release_train.autonomic_crown.model import Finding

        self.assertEqual(standing.execution_of({"standing": "ALIVE"}, []), {"state": "ALIVE"})
        self.assertEqual(standing.execution_of({"standing": "BLOCKED"}, [])["state"], "BLOCKED")
        self.assertEqual(standing.execution_of(None, [Finding("RECEIPT_UNVERIFIED", "r")])["state"], "REFUSED")
        self.assertEqual(
            standing.execution_of(None, [Finding("TRANSPORT_UNAVAILABLE", "r")]),
            {"state": "BLOCKED", "type": "TRANSPORT_FAILURE"},
        )


if __name__ == "__main__":
    unittest.main()
