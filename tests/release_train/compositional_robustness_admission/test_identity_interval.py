import unittest
from fractions import Fraction
from scripts.release_train.compositional_robustness_admission import Subject, PolicyIdentity, Interval
from scripts.release_train.compositional_robustness_admission.refusal import Refused
class T(unittest.TestCase):
    def test_exact_identity_and_interval(self):
        Subject("o/r","a"*40); PolicyIdentity(1,"b"*64); self.assertEqual(Interval(Fraction(1),Fraction(2)).width,1)
        with self.assertRaises(Refused): Subject("o/r","short")
        with self.assertRaises(Refused): Interval(Fraction(2),Fraction(1))
