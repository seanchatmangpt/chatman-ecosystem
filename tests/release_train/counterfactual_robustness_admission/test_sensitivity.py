from fractions import Fraction as F
import unittest
from scripts.release_train.counterfactual_robustness_admission import *
from scripts.release_train.counterfactual_robustness_admission.refusal import Refused
class T(unittest.TestCase):
 def test_gamma_monotone_and_manski(self):
  a=gamma_interval(F(7,10),F(1)); b=gamma_interval(F(7,10),F(2)); self.assertGreaterEqual(b.width,a.width); self.assertGreaterEqual(breakdown_gamma(F(7,10),F(1,2)),F(1)); m=manski_mean((F(1),F(0)),4); self.assertEqual((m.lower,m.upper),(F(1,4),F(3,4)))
  with self.assertRaises(Refused): gamma_interval(F(1,2),F(1,2))
