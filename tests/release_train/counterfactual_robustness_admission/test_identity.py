from datetime import datetime,timezone
from fractions import Fraction as F
import unittest
from scripts.release_train.counterfactual_robustness_admission import *
from scripts.release_train.counterfactual_robustness_admission.refusal import Refused
NOW=datetime(2026,8,23,5,35,tzinfo=timezone.utc)
class T(unittest.TestCase):
 def test_exact_identity_and_invalid(self):
  s=Subject("seanchatmangpt/chatman-ecosystem","a"*40); self.assertEqual(s.exact,"seanchatmangpt/chatman-ecosystem@"+"a"*40)
  with self.assertRaises(Refused): Subject("x","short")
  with self.assertRaises(Refused): PolicyIdentity("p",-1,"b"*64)
