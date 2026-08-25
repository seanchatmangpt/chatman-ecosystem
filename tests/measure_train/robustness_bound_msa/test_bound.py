import unittest
from fractions import Fraction
from scripts.measure_train.robustness_bound_msa.bound import RobustnessBound
from scripts.measure_train.robustness_bound_msa.subject import Refused
class T(unittest.TestCase):
 def test_domain(self):
  b=RobustnessBound(Fraction(1,4),Fraction(3,4),Fraction(2),"IPS","a"*64)
  self.assertEqual(b.width,Fraction(1,2))
  with self.assertRaises(Refused): RobustnessBound(Fraction(0),Fraction(1),Fraction(1,2),"IPS","a"*64)
