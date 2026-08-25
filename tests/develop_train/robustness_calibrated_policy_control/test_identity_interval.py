import unittest
from fractions import Fraction as F
from scripts.develop_train.robustness_calibrated_policy_control import Subject,PolicyIdentity,Interval
from scripts.develop_train.robustness_calibrated_policy_control.refusal import Refused
class T(unittest.TestCase):
 def test_exact_identity_and_interval(self):
  self.assertEqual(Subject('o/r@'+'a'*40).value[-40:],'a'*40)
  self.assertEqual(PolicyIdentity(2,'b'*64).generation,2)
  self.assertEqual(Interval(F(1,4),F(3,4)).width,F(1,2))
  with self.assertRaises(Refused): Subject('o/r@abc')
