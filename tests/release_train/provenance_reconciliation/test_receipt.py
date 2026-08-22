import unittest
from dataclasses import replace
from scripts.release_train.provenance_reconciliation.model import Refused
from scripts.release_train.provenance_reconciliation.plan import PlanStep
from scripts.release_train.provenance_reconciliation.receipt import manufacture_receipt,replay

class ReceiptCourt(unittest.TestCase):
    def test_replay(self): replay(manufacture_receipt("a"*40,["a/b@"+"b"*40],["e"],(PlanStep("a/b@"+"b"*40,"VERIFY",True),)))
    def test_tamper_refused(self):
        r=manufacture_receipt("a"*40,["a/b@"+"b"*40],["e"],(PlanStep("a/b@"+"b"*40,"VERIFY",True),))
        with self.assertRaisesRegex(Refused,"RECEIPT_TAMPERED"): replay(replace(r,digest_sha256="0"*64))
if __name__ == "__main__": unittest.main()
