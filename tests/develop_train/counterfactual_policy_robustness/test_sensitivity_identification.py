import unittest
from fractions import Fraction as F
from scripts.develop_train.counterfactual_policy_robustness.evidence import LoggedOutcome
from scripts.develop_train.counterfactual_policy_robustness.sensitivity import gamma_interval
from scripts.develop_train.counterfactual_policy_robustness.identification import manski_mean
from scripts.develop_train.counterfactual_policy_robustness.errors import Refused
class TestSensitivity(unittest.TestCase):
    def test_gamma_widens_and_manski_bounds(self):
        rows=[LoggedOutcome('a','A',F(1),F(1,2),F(1,2)),LoggedOutcome('b','A',F(0),F(1,2),F(1,2))]; one=gamma_interval(rows,F(1)); two=gamma_interval(rows,F(2)); self.assertGreater(two.width,one.width); self.assertEqual(manski_mean([F(1)],1).lower,F(1,2)); self.assertEqual(manski_mean([F(1)],1).upper,F(1))
        with self.assertRaisesRegex(Refused,'GAMMA'): gamma_interval(rows,F(1,2))
