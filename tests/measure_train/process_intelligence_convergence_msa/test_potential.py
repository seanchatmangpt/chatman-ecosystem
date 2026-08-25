import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.process_intelligence_convergence_msa.subject import Subject
from scripts.measure_train.process_intelligence_convergence_msa.obligation import ObligationState
from scripts.measure_train.process_intelligence_convergence_msa.epoch import ClosureEpoch
from scripts.measure_train.process_intelligence_convergence_msa.potential import closure_potential
class T(unittest.TestCase):
 def test_weighted_debt(self):
  e=ClosureEpoch(Subject("o/r","a"*40,1),datetime.now(timezone.utc),(ObligationState("a","PASS",1),ObligationState("b","FAIL",1)))
  self.assertEqual(closure_potential(e),Fraction(5,2))
