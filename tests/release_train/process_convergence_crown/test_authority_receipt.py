import unittest
from scripts.release_train.process_convergence_crown import ActionClass,require_broker,Receipt,replay
from scripts.release_train.process_convergence_crown.refusal import Refused

class AuthorityReceiptTest(unittest.TestCase):
    def test_consequential_requires_brce(self):
        with self.assertRaises(Refused): require_broker(ActionClass.CONSEQUENTIAL)
        self.assertEqual(require_broker(ActionClass.CONSEQUENTIAL,"BRCE"),ActionClass.CONSEQUENTIAL)
    def test_receipt_replay_and_tamper(self):
        r=Receipt("o/r@"+"a"*40,3,"MINIMAX","PARTIAL_ALIVE")
        d=r.digest(); self.assertEqual(replay(r,d),"REPLAY_MATCH")
        with self.assertRaises(Refused): replay(r,"0"*64)
