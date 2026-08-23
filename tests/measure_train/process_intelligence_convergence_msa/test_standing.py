import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject
from scripts.measure_train.process_intelligence_convergence_msa.obligation import ObligationState
from scripts.measure_train.process_intelligence_convergence_msa.epoch import ClosureEpoch
from scripts.measure_train.process_intelligence_convergence_msa.convergence import ConvergenceResult
from scripts.measure_train.process_intelligence_convergence_msa.standing import standing
class T(unittest.TestCase):
 def test_positive_ceiling(self):
  e=ClosureEpoch(Subject("o/r","a"*40,1),datetime.now(timezone.utc),(ObligationState("x","PASS"),))
  c=ConvergenceResult("CONVERGING",Fraction(1),Fraction(0),Fraction(-1),(),Fraction(1),Fraction(0))
  self.assertEqual(standing(e,c,()),"PARTIAL_ALIVE")
