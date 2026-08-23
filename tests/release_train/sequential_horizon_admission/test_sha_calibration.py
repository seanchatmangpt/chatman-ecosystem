import unittest
from fractions import Fraction
from scripts.release_train.sequential_horizon_admission import GainCalibration,Refused
class T(unittest.TestCase):
 def test_support_reliability_and_drift(self):
  GainCalibration(8,Fraction(1,10),Fraction(9,10),1,2).admit()
  with self.assertRaises(Refused): GainCalibration(8,0,1,3,2).admit()
