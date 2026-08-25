import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject
from scripts.measure_train.process_intelligence_convergence_msa.obligation import ObligationState
from scripts.measure_train.process_intelligence_convergence_msa.epoch import ClosureEpoch
from scripts.measure_train.process_intelligence_convergence_msa.hazard import transition_hazards
class T(unittest.TestCase):
 def test_discharge_hazard(self):
  now=datetime.now(timezone.utc)
  a=ClosureEpoch(Subject("o/r","a"*40,1),now,(ObligationState("x","FAIL"),))
  b=ClosureEpoch(Subject("o/r","b"*40,2),now+timedelta(seconds=1),(ObligationState("x","PASS"),))
  self.assertEqual(transition_hazards([a,b])["discharge_hazard"],Fraction(1))
