import unittest
from fractions import Fraction
from scripts.release_train.process_evidence_crown import *
class T(unittest.TestCase):
 def test_observed_only_regret(self):
  r=Realization('PARETO',1,('a',),('a','b'),Fraction(4,5),Fraction(3,5),Fraction(1,10))
  self.assertEqual(observed_regret(r,{'a':Fraction(3,5),'b':Fraction(4,5)}),Fraction(1,5))
  with self.assertRaises(Refused): observed_regret(r,{'c':Fraction(1)})
 def test_calibration_support_and_error(self):
  RealizationCalibration(1,20,Fraction(1,20),Fraction(1,20),Fraction(1,10)).admit()
  with self.assertRaises(Refused): RealizationCalibration(1,2,Fraction(0),Fraction(0),Fraction(0)).admit()
