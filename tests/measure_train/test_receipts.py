import unittest
from scripts.measure_train.receipts import manufacture
from scripts.measure_train.evidence import *
from scripts.measure_train.identity import Subject
class ReceiptCourt(unittest.TestCase):
    def test_deterministic_order_after_admission(self):
        s=Subject('o/r','a'*40); a=Evidence('a',s,EvidenceKind.CI,'2026-08-22T05:00:00Z',Outcome.PASS); b=Evidence('b',s,EvidenceKind.RUNTIME,'2026-08-22T05:00:00Z',Outcome.PASS)
        self.assertNotEqual(manufacture(s.identity,(a,b)).observation_digest,'')
    def test_receipt_never_claims_actuation(self): self.assertFalse(manufacture('o/r@'+'a'*40,()).actuation_performed)
    def test_parents_canonical(self): self.assertEqual(manufacture('x',(),('b','a')).parent_digests,('a','b'))
if __name__=='__main__': unittest.main()
