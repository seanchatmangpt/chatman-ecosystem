import unittest
from fractions import Fraction as F
from scripts.develop_train.robustness_calibrated_policy_control.calibration import BoundCalibration,calibrated_interval
from scripts.develop_train.robustness_calibrated_policy_control.frontier import CalibrationFrontier
from scripts.develop_train.robustness_calibrated_policy_control.interval import Interval
from scripts.develop_train.robustness_calibrated_policy_control.refusal import Refused
class T(unittest.TestCase):
 def test_current_and_widening(self):
  c=BoundCalibration(3,'c'*64,10,F(9,10),F(1,5),F(2,5)); f=CalibrationFrontier((c,))
  self.assertTrue(c.admitted(3,F(4,5),F(1,2)))
  self.assertEqual(calibrated_interval(Interval(F(0),F(1)),c,F(1,2)).width,F(11,10))
  self.assertEqual(f.require(3,'c'*64),c)
 def test_divergence(self):
  a=BoundCalibration(4,'a'*64,5,F(1),F(0),F(0)); b=BoundCalibration(4,'b'*64,5,F(1),F(0),F(0))
  with self.assertRaises(Refused): CalibrationFrontier((a,b)).current()
