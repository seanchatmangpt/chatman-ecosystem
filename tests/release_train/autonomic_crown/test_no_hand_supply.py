"""The NEW_HEAD re-evidence edge is supplied by hand; the court may not be told otherwise."""

from __future__ import annotations

import copy
import unittest

from _autonomic_support import AUTONOMY, committed_evaluation, committed_inputs, load

from scripts.release_train.autonomic_crown import edges


class NoHandSupplyTest(unittest.TestCase):
    def setUp(self):
        self.inputs = committed_inputs(self)
        self.doc = load(AUTONOMY / "edges.json")
        self.rep = next(e for e in self.doc["edges"] if e["id"] == "E-REP-01")

    def test_re_evidence_edge_is_recorded_as_hand_supplied(self):
        self.assertEqual(self.rep["stage"], "repair")
        self.assertEqual(self.rep["owner_kinds"], ["llm", "human"])
        self.assertTrue(self.rep["evidence"]["locator"].endswith(":tests/release_train/root_crown/test_loop.py"))
        self.assertTrue(edges.is_operational_dependency(self.rep))

    def test_located_bytes_witness_hand_built_observations(self):
        data = self.inputs.source.resolve(self.rep["evidence"]["locator"]).decode("utf-8")
        self.assertIn("def test_re_evidenced_new_head_restores_alive", data)
        self.assertIn('obs["repos"][XAAS]["head_sha"] = NEW', data)

    def test_relabeling_it_machine_is_refused(self):
        doc = copy.deepcopy(self.doc)
        for e in doc["edges"]:
            if e["id"] == "E-REP-01":
                e["owner_kind"], e["owner_kinds"] = "machine", ["machine"]
        rep = edges.check(doc, self.inputs.source, doc["crown_subject"])
        self.assertIn(("OWNER_KIND_UNWITNESSED", "E-REP-01"), {(f.code, f.subject) for f in rep.findings})

    def test_hand_supply_blocks_u02_and_u14(self):
        g = {x.id: x for x in committed_evaluation(self).gates}
        self.assertIn("E-REP-01", g["U-02"].findings)
        self.assertIn("edge:E-REP-01:hand-supplied-repair", g["U-14"].findings)


if __name__ == "__main__":
    unittest.main()
