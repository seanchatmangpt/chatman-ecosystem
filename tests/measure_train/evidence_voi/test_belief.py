import unittest
from fractions import Fraction
from scripts.measure_train.evidence_voi.belief import BeliefState
from scripts.measure_train.evidence_voi.subject import Refused
class T(unittest.TestCase):
 def test_probability_bounds(self):
  self.assertEqual(BeliefState(Fraction(1,2),0).p_not_alive,Fraction(1,2))
  with self.assertRaises(Refused): BeliefState(Fraction(3,2),0)
