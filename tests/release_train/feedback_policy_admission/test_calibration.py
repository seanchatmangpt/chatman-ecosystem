import unittest
from fractions import Fraction
from fixture import *
from scripts.release_train.feedback_policy_admission.calibration import GainCalibration
from scripts.release_train.feedback_policy_admission.drift import detect
from scripts.release_train.feedback_policy_admission.errors import Refused
class T(unittest.TestCase):
 def test_reliable_and_drift(self):
  c=GainCalibration.from_residuals((Fraction(0),)*3).admit()
  self.assertEqual(c.mae,0)
  with self.assertRaises(Refused): GainCalibration.from_residuals((Fraction(1,2),)*3).admit()
  self.assertTrue(detect((Fraction(1,3),)*4).drifted)
if __name__=="__main__": unittest.main()
