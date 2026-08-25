import unittest
from fractions import Fraction
from scripts.measure_train.robustness_bound_msa.bound import RobustnessBound
from scripts.measure_train.robustness_bound_msa.geometry import interval_iou,identification_value
class T(unittest.TestCase):
 def test_geometry(self):
  a=RobustnessBound(Fraction(0),Fraction(1,2),Fraction(1),"A","a"*64)
  b=RobustnessBound(Fraction(1,4),Fraction(3,4),Fraction(1),"B","b"*64)
  self.assertEqual(interval_iou(a,b),Fraction(1,3))
  self.assertEqual(identification_value(a,Fraction(1)),Fraction(1,2))
