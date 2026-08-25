import unittest
from scripts.release_train.process_trace_crown import ActionClass, Receipt, replay
from scripts.release_train.process_trace_crown.authority import admit
from scripts.release_train.process_trace_crown.refusal import Refused

class TestAuthorityReceipt(unittest.TestCase):
    def test_direct_do_refuses(self):
        with self.assertRaises(Refused): admit(ActionClass.DO)
    def test_receipt_tamper_refuses(self):
        r=Receipt("a/b@"+"1"*40,"2"*64,"PARTIAL_ALIVE")
        d=r.digest
        replay(r,d)
        mutated=Receipt(r.subject_key,r.trace_digest,"ALIVE")
        with self.assertRaises(Refused): replay(mutated,d)
