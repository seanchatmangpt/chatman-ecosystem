import unittest
from fractions import Fraction
from scripts.measure_train.robustness_bound_msa.calibration import BoundCalibration
from scripts.measure_train.robustness_bound_msa.standing import standing
class T(unittest.TestCase):
 def test_ceiling_and_blocker(self):
  c=BoundCalibration(5,Fraction(1),Fraction(1,2),Fraction(0),"CALIBRATED")
  self.assertEqual(standing([c]),"PARTIAL_ALIVE")
  self.assertEqual(standing([c],["BUILD_BROKEN"]),"BLOCKED")
