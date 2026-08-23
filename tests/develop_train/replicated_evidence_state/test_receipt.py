import unittest
from scripts.develop_train.replicated_evidence_state.receipt import Receipt
from scripts.develop_train.replicated_evidence_state.replay import replay

class ReceiptTest(unittest.TestCase):
    def test_replay_rejects_tamper_and_actuation(self):
        r=Receipt("o/r@"+"a"*40,1,"b"*64,"c"*64,"PARTIAL_ALIVE",False); d=r.digest()
        self.assertTrue(replay(r,d))
        self.assertFalse(replay(Receipt(r.subject,2,r.value_digest,r.merkle_root,r.standing,False),d))
        self.assertFalse(replay(Receipt(r.subject,1,r.value_digest,r.merkle_root,r.standing,True),d))
