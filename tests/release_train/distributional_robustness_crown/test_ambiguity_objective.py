import unittest
from fractions import Fraction
from scripts.release_train.distributional_robustness_crown.api import *
class T(unittest.TestCase):
 def test_worst_case_witness(self):
  r=Distribution.from_mapping({"good":3,"bad":1}); amb=AmbiguitySet(Kind.TV,Fraction(1,4),r); cs=tv_extremes(r,Fraction(1,4)); w=worst_case(amb,cs,{"good":0,"bad":4}); self.assertEqual(w.value,2); self.assertEqual(w.witness.mapping()["bad"],Fraction(1,2))
