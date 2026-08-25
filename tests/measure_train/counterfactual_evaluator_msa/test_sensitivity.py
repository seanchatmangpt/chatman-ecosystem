import unittest
from fractions import Fraction
from scripts.measure_train.counterfactual_evaluator_msa.sensitivity import sensitivity_profile
class T(unittest.TestCase):
 def test_shift(self):
  p=sensitivity_profile(Fraction(1,2),[Fraction(2,5),Fraction(3,5)])
  self.assertEqual(p.max_shift,Fraction(1,10))
