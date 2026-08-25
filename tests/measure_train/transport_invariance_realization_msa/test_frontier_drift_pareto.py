import unittest
from fractions import Fraction
from scripts.measure_train.transport_invariance_realization_msa.frontier import StressCalibrationModel,current
from scripts.measure_train.transport_invariance_realization_msa.drift import Cusum
from scripts.measure_train.transport_invariance_realization_msa.pareto import Candidate,frontier,frontier_jaccard
from scripts.measure_train.transport_invariance_realization_msa.refusal import Refused
class T(unittest.TestCase):
 def test_current_drift_and_frontier_stability(self):
  a=StressCalibrationModel(1,"a"*64,10,0.1,0.1,"CALIBRATED"); b=StressCalibrationModel(2,"b"*64,20,0.1,0.1,"CALIBRATED")
  self.assertEqual(current([a,b]),b)
  with self.assertRaises(Refused): current([b,StressCalibrationModel(2,"c"*64,20,0.1,0.1,"CALIBRATED")])
  c=Cusum(Fraction(1,5)); c.update(Fraction(3,10),Fraction(1,10)); self.assertTrue(c.changed)
  p1=Candidate("a",Fraction(1,10),Fraction(0),Fraction(1,10),Fraction(1,10)); p2=Candidate("b",Fraction(2,10),Fraction(1,10),Fraction(2,10),Fraction(2,10))
  self.assertEqual(frontier([p1,p2]),(p1,)); self.assertEqual(frontier_jaccard([p1],[p1,p2]),Fraction(1,2))
