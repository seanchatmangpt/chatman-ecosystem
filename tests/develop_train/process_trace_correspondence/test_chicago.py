import unittest
from scripts.develop_train.process_trace_correspondence import *
class T(unittest.TestCase):
 def test_full_methodology_path(self):
  s=Subject("o/r@"+"f"*40); rails=[RailEvidence(r,s.value,"sem","trace",7) for r in Rail]; current=[Currentness(7,10,20) for _ in rails]; q=TraceCorrespondenceEngine().qualify(s,rails,current,Coverage(METHODOLOGIES),15)
  self.assertEqual(q.standing,"PARTIAL_ALIVE"); self.assertFalse(q.receipt.actuation_performed); self.assertTrue(replay(q.receipt,q.receipt.body,q.receipt.digest))
 def test_failure_dominates(self):
  s=Subject("o/r@"+"1"*40); rails=[RailEvidence(r,s.value,"sem","trace",7) for r in Rail]; current=[Currentness(7,10,20) for _ in rails]; q=TraceCorrespondenceEngine().qualify(s,rails,current,Coverage(METHODOLOGIES),15,["TLS_CONTRADICTION"]); self.assertEqual(q.standing,"UNKNOWN"); self.assertIsNone(q.receipt)
