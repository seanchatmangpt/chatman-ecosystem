import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject
from scripts.measure_train.process_intelligence_convergence_msa.obligation import ObligationState
from scripts.measure_train.process_intelligence_convergence_msa.epoch import ClosureEpoch
from scripts.measure_train.process_intelligence_convergence_msa.oscillation import obligation_oscillations
class T(unittest.TestCase):
 def test_pass_fail_pass_is_oscillation(self):
  now=datetime.now(timezone.utc)
  rows=[ClosureEpoch(Subject("o/r",c*40,i+1),now+timedelta(seconds=i),(ObligationState("x",s),)) for i,(c,s) in enumerate([("a","PASS"),("b","FAIL"),("c","PASS")])]
  self.assertTrue(obligation_oscillations(rows)["x"]["oscillating"])
