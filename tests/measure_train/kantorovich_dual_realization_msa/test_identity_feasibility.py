import unittest
from fractions import Fraction
from scripts.measure_train.kantorovich_dual_realization_msa.subject import Subject
from scripts.measure_train.kantorovich_dual_realization_msa.certificate import Certificate
from scripts.measure_train.kantorovich_dual_realization_msa.errors import Refused
class T(unittest.TestCase):
 def test_identity_and_gap(self):
  self.assertEqual(Subject("o/r","a"*40,"b"*64).repo,"o/r")
  self.assertEqual(Certificate(Fraction(1),Fraction(1),Fraction(0),Fraction(0),"c"*64,"d"*64).gap,0)
  with self.assertRaises(Refused): Subject("o/r","bad","b"*64)
