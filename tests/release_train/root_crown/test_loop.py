"""Self-feeding loop R_t -> O*_{t+1}: hash chain, NEW_HEAD cascade, genesis."""

from __future__ import annotations

import copy
import unittest

from _support import CROWN_SHA, alive_observations, alive_tree

from scripts.release_train.root_crown import crown

XAAS = "seanchatmangpt/xaas"
NEW = "9" * 40


class LoopTest(unittest.TestCase):
    def setUp(self):
        self.tree = alive_tree()
        self.obs = alive_observations(self.tree)
        self.r0 = crown.evaluate(self.tree.release_dir, self.obs, None, CROWN_SHA, root=self.tree.root)

    def tearDown(self):
        self.tree.cleanup()

    def test_genesis_is_lawful(self):
        self.assertEqual(self.r0.standing, "ALIVE")
        self.assertTrue(self.r0.receipt["genesis"])
        self.assertIsNone(self.r0.receipt["previous_receipt_digest"])
        self.assertEqual(self.r0.receipt["heads"][XAAS], self.obs["repos"][XAAS]["head_sha"])

    def test_unchanged_heads_chain_and_stay_alive(self):
        r1 = crown.evaluate(self.tree.release_dir, self.obs, self.r0.receipt, CROWN_SHA, root=self.tree.root)
        self.assertEqual(r1.standing, "ALIVE")
        self.assertEqual(r1.receipt["previous_receipt_digest"], self.r0.receipt["receipt_digest"])
        self.assertTrue(crown.verify_receipt(r1.receipt))

    def test_moved_head_drops_affected_pass_to_unknown(self):
        obs = copy.deepcopy(self.obs)
        obs["repos"][XAAS]["head_sha"] = NEW
        obs["repos"][XAAS]["compare_status"] = "ahead"
        # xaas receipts still name the old subject (ahead of it is lineage-valid, but not the new head).
        for locator, art in obs["artifacts"].items():
            if locator.startswith(XAAS + ":"):
                art["subject_compare"] = "ahead"
        r1 = crown.evaluate(self.tree.release_dir, obs, self.r0.receipt, CROWN_SHA, root=self.tree.root)
        affected = {r.id for r in self.tree.inputs().requirements if XAAS in {r.owner_repo, r.locator_repo}}
        self.assertEqual(affected, {"AC-13", "AC-14", "F-09", "F-12"})
        unknown = {k for k, v in r1.receipt["requirements"].items() if v["state"] == "UNKNOWN"}
        self.assertEqual(unknown, affected)
        for rid in affected:
            self.assertEqual(r1.receipt["requirements"][rid]["code"], "NEW_HEAD_UNEVIDENCED")
        self.assertEqual(r1.standing, "BLOCKED")
        self.assertEqual(set(r1.receipt["next_observations"]["cascade"]) & affected, affected)
        self.assertEqual(r1.receipt["previous_receipt_digest"], self.r0.receipt["receipt_digest"])

    def test_re_evidenced_new_head_restores_alive(self):
        obs = copy.deepcopy(self.obs)
        obs["repos"][XAAS]["head_sha"] = NEW
        for locator, art in obs["artifacts"].items():
            if locator.startswith(XAAS + ":"):
                art["json"]["subject_sha"] = NEW
                art["subject_compare"] = "identical"
        r1 = crown.evaluate(self.tree.release_dir, obs, self.r0.receipt, CROWN_SHA, root=self.tree.root)
        self.assertEqual(r1.standing, "ALIVE", r1.remaining)

    def test_broken_chain_refuses(self):
        forged = dict(self.r0.receipt, standing="ALIVE", heads={})
        r1 = crown.evaluate(self.tree.release_dir, self.obs, forged, CROWN_SHA, root=self.tree.root)
        self.assertEqual(r1.standing, "REFUSED")
        self.assertTrue(any(r.startswith("REFUSED:RECEIPT_CHAIN_BROKEN") for r in r1.refusals))


if __name__ == "__main__":
    unittest.main()
