import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject,Refused
from scripts.measure_train.process_intelligence_convergence_msa.obligation import ObligationState
from scripts.measure_train.process_intelligence_convergence_msa.epoch import ClosureEpoch
from scripts.measure_train.process_intelligence_convergence_msa.admission import admit
class T(unittest.TestCase):
 def test_obligation_universe_drift_refuses(self):
  now=datetime.now(timezone.utc)
  a=ClosureEpoch(Subject("o/r","a"*40,1),now,(ObligationState("x","PASS"),))
  b=ClosureEpoch(Subject("o/r","b"*40,2),now+timedelta(seconds=1),(ObligationState("y","PASS"),))
  with self.assertRaises(Refused): admit([a,b],now+timedelta(seconds=2),100)
