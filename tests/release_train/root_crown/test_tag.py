"""Tag legality (RFC-0004 §45): LEGAL only for ALIVE ∧ head == crown_sha ∧ tag absent/equal."""

from __future__ import annotations

import unittest

from _support import CROWN_SHA, alive_observations, alive_tree

from scripts.release_train.root_crown import crown
from scripts.release_train.root_crown.model import TAG_RULES
from scripts.release_train.root_crown.tag import tag_decision


class TagTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = alive_tree()
        try:
            cls.alive = crown.evaluate(
                tree.release_dir, alive_observations(tree), None, CROWN_SHA, root=tree.root
            ).receipt
        finally:
            tree.cleanup()

    def test_alive_equal_sha_absent_tag_is_legal(self):
        self.assertEqual(self.alive["standing"], "ALIVE")
        decision = tag_decision(self.alive, CROWN_SHA, None, "v26.9.25")
        self.assertEqual((decision["decision"], decision["reasons"]), ("LEGAL", []))

    def test_existing_equal_tag_is_idempotently_legal(self):
        self.assertEqual(tag_decision(self.alive, CROWN_SHA, CROWN_SHA, "v26.9.25")["decision"], "LEGAL")

    def test_one_illegal_mutant_per_reason(self):
        not_alive = dict(self.alive, standing="BLOCKED")
        not_alive["receipt_digest"] = crown.receipt_digest_of(not_alive)
        table = {
            "CROWN_NOT_ALIVE": (not_alive, CROWN_SHA, None),
            "SHA_MISMATCH": (self.alive, "d" * 40, None),
            "TAG_EXISTS_ELSEWHERE": (self.alive, CROWN_SHA, "e" * 40),
            "RECEIPT_UNVERIFIED": (dict(self.alive, receipt_digest="sha256:" + "0" * 64), CROWN_SHA, None),
        }
        self.assertEqual(set(table), set(TAG_RULES))
        for reason, (receipt, head, existing) in table.items():
            with self.subTest(reason=reason):
                decision = tag_decision(receipt, head, existing, "v26.9.25")
                self.assertEqual(decision["decision"], "ILLEGAL")
                self.assertEqual([r.split(":")[1] for r in decision["reasons"]], [reason])


if __name__ == "__main__":
    unittest.main()
