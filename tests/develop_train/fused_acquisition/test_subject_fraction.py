import unittest
from fractions import Fraction
from scripts.develop_train.fused_acquisition.subject import Subject
from scripts.develop_train.fused_acquisition.fractions import unit, positive
from scripts.develop_train.fused_acquisition.refusals import Refused
class TestSubjectFraction(unittest.TestCase):
 def test_exact_subject_and_fraction_bounds(self):
  self.assertEqual(Subject('seanchatmangpt/chatman-ecosystem','a'*40).identity,'seanchatmangpt/chatman-ecosystem@'+'a'*40)
  self.assertEqual(unit(Fraction(1,3),'x'),Fraction(1,3)); self.assertEqual(positive(2,'x'),2)
  with self.assertRaises(Refused): Subject('bad','abc')
  with self.assertRaises(Refused): unit(2,'x')
  with self.assertRaises(Refused): positive(0,'x')
