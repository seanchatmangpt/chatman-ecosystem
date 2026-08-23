import unittest
from fractions import Fraction
from scripts.measure_train.validation_independence_realization_msa.drift import cusum_false_independence
from scripts.measure_train.validation_independence_realization_msa.inflation import information_inflation,duplicate_capital_multiplier
class T(unittest.TestCase):
 def test_drift_and_false_precision(self):
  self.assertTrue(cusum_false_independence([False]*10+[True]).alarm)
  self.assertEqual(information_inflation(Fraction(1,2),Fraction(1,4)),Fraction(1,2))
  self.assertEqual(duplicate_capital_multiplier(2,6),3)
