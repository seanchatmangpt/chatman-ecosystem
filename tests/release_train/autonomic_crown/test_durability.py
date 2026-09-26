"""U-11 (cold reconstruction) and U-14 (hidden local state) scans on real committed bytes."""

from __future__ import annotations

import unittest

from _autonomic_support import AUTONOMY, RELEASE_DIR, WORKFLOW, committed_evaluation, load

from scripts.release_train.autonomic_crown import durability

OBS = RELEASE_DIR / "hardening" / "receipts" / "run-36161856985" / "observations.json"


class DurabilityTest(unittest.TestCase):
    def setUp(self):
        self.edges = load(AUTONOMY / "edges.json")["edges"]

    def test_actions_artifact_chain_is_not_durable(self):
        found = durability.non_durable_receipts(WORKFLOW.read_text(encoding="utf-8"), self.edges)
        self.assertIn("edge:E-CONT-01:actions-artifact", found)
        self.assertTrue(any(f.endswith(":artifact-retention") for f in found))
        self.assertTrue(any(f.endswith(":chain-parent-from-artifact") for f in found))

    def test_durable_inputs_have_no_findings(self):
        durable = [e for e in self.edges if e["id"] != "E-CONT-01"]
        self.assertEqual(durability.non_durable_receipts("jobs:\n  a:\n    steps: []\n", durable), [])

    def test_operator_local_state_is_hidden_state(self):
        found = durability.hidden_local_state(load(OBS), self.edges)
        self.assertEqual(
            found,
            [
                "edge:E-OBS-02:hand-supplied-observe",
                "edge:E-REP-01:hand-supplied-repair",
                "observations:local_worktrees:operator-local",
                "observations:private_repos:operator-local",
            ],
        )
        machine_only = [e for e in self.edges if e["owner_kinds"] == ["machine"]]
        self.assertEqual(durability.hidden_local_state({"repos": {}}, machine_only), [])

    def test_gates(self):
        ev = committed_evaluation(self)
        g = {x.id: x for x in ev.gates}
        self.assertEqual((g["U-11"].state, g["U-11"].code), ("BLOCKED", "NON_DURABLE_RECEIPT_STORE"))
        self.assertEqual((g["U-14"].state, g["U-14"].code), ("BLOCKED", "HIDDEN_LOCAL_STATE"))


if __name__ == "__main__":
    unittest.main()
