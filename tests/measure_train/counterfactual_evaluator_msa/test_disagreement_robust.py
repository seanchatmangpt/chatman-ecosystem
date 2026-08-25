import unittest
from fractions import Fraction
from scripts.measure_train.counterfactual_evaluator_msa.robust import median,median_absolute_deviation
class T(unittest.TestCase):
 def test_median_robust(self):
  xs=[Fraction(1,2),Fraction(11,20),Fraction(9,10)]
  self.assertEqual(median(xs),Fraction(11,20)); self.assertEqual(median_absolute_deviation(xs),Fraction(1,20))
