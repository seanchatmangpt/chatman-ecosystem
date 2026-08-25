import unittest
from datetime import datetime,timezone
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject,Refused
from scripts.measure_train.process_intelligence_convergence_msa.obligation import ObligationState
from scripts.measure_train.process_intelligence_convergence_msa.epoch import ClosureEpoch
class T(unittest.TestCase):
 def test_duplicate_obligation_refuses(self):
  s=Subject("o/r","a"*40,1); now=datetime.now(timezone.utc)
  with self.assertRaises(Refused): ClosureEpoch(s,now,(ObligationState("x","PASS"),ObligationState("x","FAIL")))
