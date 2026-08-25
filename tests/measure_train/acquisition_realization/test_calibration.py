import unittest
from fractions import Fraction
from scripts.measure_train.acquisition_realization.realization import RealizedInformation
from scripts.measure_train.acquisition_realization.calibration import calibrate
class T(unittest.TestCase):
 def test_support_and_error(self):
  r=RealizedInformation(Fraction(1,5),0.2,0.0,"POSITIVE")
  self.assertEqual(calibrate([r]*4).calibration_state,"INSUFFICIENT")
  self.assertEqual(calibrate([r]*5).calibration_state,"CALIBRATED")
  bad=RealizedInformation(Fraction(1,5),0.8,0.6,"POSITIVE")
  self.assertEqual(calibrate([bad]*5).calibration_state,"UNRELIABLE")
