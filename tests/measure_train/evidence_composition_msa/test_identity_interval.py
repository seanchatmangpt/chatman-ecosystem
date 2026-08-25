import unittest
from fractions import Fraction
from scripts.measure_train.evidence_composition_msa.subject import Subject,Refused
from scripts.measure_train.evidence_composition_msa.interval import Interval,frechet_and,independent_and
class T(unittest.TestCase):
 def test_identity_and_bounds(self):
  s=Subject("o/r","a"*40,"b"*64); self.assertEqual(s.repo,"o/r")
  a=Interval(Fraction(1,2),Fraction(4,5)); b=Interval(Fraction(1,2),Fraction(3,4))
  self.assertEqual(frechet_and(a,b).lower,Fraction(0))
  self.assertEqual(independent_and(a,b).lower,Fraction(1,4))
  with self.assertRaises(Refused): Subject("o/r","bad","b"*64)
