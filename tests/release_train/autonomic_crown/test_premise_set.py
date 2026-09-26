"""U-12 first test (RFC-0005 §10.4): Berthier recompile for the premise set {RFC-0004, RFC-0005}.

Runs the real strategic compiler (root_crown.projector + berthier) on the committed
v26.9.25 inputs; no git object database is needed.
"""

from __future__ import annotations

import json
import unittest

from _autonomic_support import AUTONOMY, RELEASE_DIR

from scripts.release_train.autonomic_crown import premise
from scripts.release_train.root_crown import berthier, projector
from scripts.release_train.root_crown.requirements import premise_sections


class PremiseSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = projector.load_inputs(RELEASE_DIR)
        cls.rfc5 = (AUTONOMY / "imports" / "RFC-0005.md").read_text(encoding="utf-8")
        cls.report = premise.run(cls.inputs, cls.rfc5)

    def test_u12_recompile_closes_with_zero_manual_restatement(self):
        r = self.report
        self.assertEqual(r["manual_restatement_count"], 0)
        self.assertEqual(r["recompile"]["standing"], "ALIVE", r["recompile"]["refusals"])
        self.assertEqual(r["recompile"]["required_owners"], ["seanchatmangpt/chatman-ecosystem"])
        self.assertEqual(r["recompile"]["affected_owners"], r["recompile"]["required_owners"])
        # 15 RFC-0005 sections + 18 derived gate requirements enter the strategic delta.
        self.assertEqual(r["recompile"]["strategic_delta"], len(premise_sections(self.rfc5)) + 18)
        self.assertTrue(r["objective_mutation"]["stale_matches_dependents"])
        self.assertEqual(r["objective_mutation"]["recompile_standing"], "ALIVE")
        self.assertEqual(len(r["objective_mutation"]["dependents"]), 18)
        self.assertTrue(r["ok"])

    def test_refusing_mutants_are_killed(self):
        for token in ("OMITTED_SUBJECT", "STALE_PROJECTION", "PREMISE_UNBOUND", "AUTHORITY_INCREASE"):
            with self.subTest(token=token):
                m = self.report["mutants"][token]
                self.assertTrue(m["emitted"], token)
                self.assertFalse(m["control_emitted"], token)
                self.assertTrue(m["killed"], token)

    def test_single_premise_output_is_byte_identical(self):
        self.assertTrue(self.report["single_premise_identical"])
        self.assertEqual(projector.check(RELEASE_DIR), [])
        text = self.inputs.rfc_text
        self.assertEqual(
            berthier.source_digests(text, self.inputs.requirements),
            berthier.source_digests({"RFC-0004": text}, self.inputs.requirements),
        )

    def test_premise_keys_and_refs(self):
        self.assertEqual(berthier.split_ref("RFC-0005§7"), ("RFC-0005", "§7"))
        self.assertEqual(berthier.split_ref("§48"), ("RFC-0004", "§48"))
        self.assertEqual(berthier.premise_key("§7", "RFC-0005"), "premise:RFC-0005#§7")
        self.assertEqual(berthier.premise_key("§48"), "premise:RFC-0004#§48")
        self.assertEqual(berthier.premise_ref_key("RFC-0005§10"), "premise:RFC-0005#§10")
        both = berthier.source_digests({"RFC-0004": self.inputs.rfc_text, "RFC-0005": self.rfc5}, ())
        self.assertIn("premise:RFC-0005#§7", both)
        self.assertIn("premise:RFC-0004#§48", both)

    def test_premise_set_digest_is_over_the_mapping(self):
        texts = {"RFC-0004": self.inputs.rfc_text, "RFC-0005": self.rfc5}
        self.assertEqual(self.report["premise_set_digest"], berthier.premise_set_digest(texts))
        self.assertNotEqual(
            berthier.premise_set_digest(texts), berthier.premise_set_digest({"RFC-0004": self.inputs.rfc_text})
        )

    def test_mutated_rfc5_breaks_the_recompile_evidence(self):
        """Anti-vacuity: the committed gate rows are not what a different premise derives."""
        section = premise_sections(self.rfc5)["§7"]
        mutated = self.rfc5.replace("| U-18 | clean cycles |", "| U-18 | clean cycle |", 1)
        self.assertNotEqual(mutated, self.rfc5)
        rows = [r.acceptance for r in premise.gate_requirements(mutated)]
        self.assertNotEqual(rows, [r.acceptance for r in premise.gate_requirements(self.rfc5)])
        self.assertIn("U-18", section)
        json.dumps(self.report)  # the report is plain JSON


if __name__ == "__main__":
    unittest.main()
