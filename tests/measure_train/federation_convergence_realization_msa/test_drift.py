import unittest
from fractions import Fraction
from scripts.measure_train.federation_convergence_realization_msa.drift import cusum
class T(unittest.TestCase):
 def test_drift(self):
  self.assertTrue(cusum([Fraction(1,2),Fraction(1,2)],threshold=Fraction(1)))
  self.assertFalse(cusum([Fraction(0),Fraction(0)],threshold=Fraction(1)))
