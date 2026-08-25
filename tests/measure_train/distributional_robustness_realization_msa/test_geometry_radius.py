import unittest
from fractions import Fraction
from scripts.measure_train.distributional_robustness_realization_msa.distribution import Distribution
from scripts.measure_train.distributional_robustness_realization_msa.geometry import tv,hellinger,chi_square,w1_two_support
from scripts.measure_train.distributional_robustness_realization_msa.radius import empirical_radius,radius_miss_rate
from scripts.measure_train.distributional_robustness_realization_msa.refusal import Refused
class T(unittest.TestCase):
 def test_geometries_radius(self):
  a=Distribution((("x",Fraction(3,4)),("y",Fraction(1,4)))); b=Distribution((("x",Fraction(1,2)),("y",Fraction(1,2))))
  self.assertEqual(tv(a,b),Fraction(1,4)); self.assertGreater(hellinger(a,b),0); self.assertGreater(chi_square(a,b),0); self.assertEqual(w1_two_support(a,b,Fraction(2)),Fraction(1,2))
  distances=[Fraction(1,10),Fraction(2,10),Fraction(3,10),Fraction(4,10)]
  self.assertEqual(empirical_radius(distances,Fraction(3,4)),Fraction(3,10)); self.assertEqual(radius_miss_rate(distances,Fraction(3,10)),Fraction(1,4))
  bad=Distribution((("x",Fraction(0)),("y",Fraction(1))))
  with self.assertRaisesRegex(Refused,"CHI_SQUARE_POSITIVITY"): chi_square(a,bad)
