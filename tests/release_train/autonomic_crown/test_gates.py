"""gates.json is the RFC-0005 §7 table: any drift is REFUSED:GATE_COVERAGE_GAP."""

from __future__ import annotations

import copy
import unittest

from _autonomic_support import AUTONOMY, load

from scripts.release_train.autonomic_crown import gates
from scripts.release_train.autonomic_crown.model import GATE_IDS


class GatesTest(unittest.TestCase):
    def setUp(self):
        self.rfc = (AUTONOMY / "imports" / "RFC-0005.md").read_text(encoding="utf-8")
        self.doc = load(AUTONOMY / "gates.json")

    def test_committed_gates_are_the_premise_table(self):
        self.assertEqual(gates.coverage(self.doc, self.rfc), [])
        self.assertEqual([g["id"] for g in self.doc["gates"]], list(GATE_IDS))
        self.assertEqual(self.doc, gates.project(self.rfc))
        self.assertEqual(self.doc["gates"][16]["threshold"], "false")
        self.assertEqual(self.doc["gates"][17]["threshold"], "3/3")

    def test_drift_is_refused(self):
        cases = {
            "dropped": lambda d: d["gates"].pop(4),
            "extra": lambda d: d["gates"].append(dict(d["gates"][0], id="U-19")),
            "relaxed": lambda d: d["gates"][1].update(threshold="1"),
            "renamed": lambda d: d["gates"][6].update(name="some mutants"),
            "duplicate": lambda d: d["gates"].append(dict(d["gates"][0])),
        }
        for name, fn in cases.items():
            with self.subTest(case=name):
                doc = copy.deepcopy(self.doc)
                fn(doc)
                self.assertIn("GATE_COVERAGE_GAP", {f.code for f in gates.coverage(doc, self.rfc)})

    def test_premise_drift_is_refused(self):
        drifted = self.rfc.replace(
            "| U-18 | clean cycles | independent clean cycles | 3/3 |",
            "| U-18 | clean cycles | independent clean cycles | 2/3 |",
        )
        self.assertNotEqual(drifted, self.rfc)
        self.assertIn("GATE_COVERAGE_GAP", {f.code for f in gates.coverage(self.doc, drifted)})


if __name__ == "__main__":
    unittest.main()
