import unittest
from fractions import Fraction
from scripts.release_train.distributional_robustness_crown.api import *
from scripts.release_train.distributional_robustness_crown.geometry import total_variation,chi_square,wasserstein1
from scripts.release_train.distributional_robustness_crown.refusal import Refused
class T(unittest.TestCase):
 def test_exact_identity_and_geometry(self):
  s=Subject("o/r","a"*40,"x",1); self.assertIn("@",s.identity)
  a=Distribution.from_mapping({"x":3,"y":1}); b=Distribution.from_mapping({"x":1,"y":1})
  self.assertEqual(total_variation(a,b),Fraction(1,4)); self.assertGreater(chi_square(a,b),0); self.assertEqual(wasserstein1(a,b,{("x","y"):2}),Fraction(1,2))
 def test_positivity_refuses(self):
  with self.assertRaises(Refused): chi_square(Distribution.from_mapping({"z":1}),Distribution.from_mapping({"x":1}))
