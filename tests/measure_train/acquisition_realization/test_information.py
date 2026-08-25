import unittest
from fractions import Fraction
from scripts.measure_train.acquisition_realization.belief import entropy_reduction
class T(unittest.TestCase):
 def test_entropy_direction(self):
  self.assertGreater(entropy_reduction(Fraction(1,2),Fraction(1,10)),0)
  self.assertLess(entropy_reduction(Fraction(1,10),Fraction(1,2)),0)
