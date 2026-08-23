import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject
from scripts.measure_train.process_intelligence_convergence_msa.obligation import ObligationState
from scripts.measure_train.process_intelligence_convergence_msa.epoch import ClosureEpoch
from scripts.measure_train.process_intelligence_convergence_msa.convergence import analyze
class T(unittest.TestCase):
 def test_monotone_discharge_converges(self):
  now=datetime.now(timezone.utc)
  a=ClosureEpoch(Subject("o/r","a"*40,1),now,(ObligationState("x","FAIL"),ObligationState("y","PASS")))
  b=ClosureEpoch(Subject("o/r","b"*40,2),now+timedelta(seconds=1),(ObligationState("x","PASS"),ObligationState("y","PASS")))
  self.assertEqual(analyze([a,b]).direction,"CONVERGING")
