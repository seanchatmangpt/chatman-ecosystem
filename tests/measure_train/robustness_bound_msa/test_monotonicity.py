import unittest
from fractions import Fraction
from scripts.measure_train.robustness_bound_msa.bound import RobustnessBound
from scripts.measure_train.robustness_bound_msa.monotonicity import check_gamma_monotonicity
class T(unittest.TestCase):
 def test_widening(self):
  a=RobustnessBound(Fraction(1,4),Fraction(3,4),Fraction(1),"IPS","a"*64)
  b=RobustnessBound(Fraction(1,5),Fraction(4,5),Fraction(2),"IPS","a"*64)
  self.assertTrue(check_gamma_monotonicity([a,b]))
