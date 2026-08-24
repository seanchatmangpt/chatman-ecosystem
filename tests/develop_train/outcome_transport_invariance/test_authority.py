import unittest
from scripts.develop_train.outcome_transport_invariance import *

S = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "a" * 40 + "#" + "b" * 64)

class AuthorityReceipt(unittest.TestCase):
    def test_brce_and_replay(self):
        with self.assertRaises(Refused):
            admit(Action.DO)
        self.assertEqual(admit(Action.DO, "BRCE"), Action.DO)
        receipt = Receipt(S.key, "MINIMAX", "PARTIAL_ALIVE", "e" * 64)
        self.assertEqual(replay(receipt, receipt.digest), "REPLAY_MATCH")
        with self.assertRaises(Refused):
            replay(receipt, "0" * 64)
