import unittest
from fractions import Fraction as F
from scripts.develop_train.counterfactual_policy_robustness.evidence import LoggedOutcome
from scripts.develop_train.counterfactual_policy_robustness.estimators import Estimator,estimate
from scripts.develop_train.counterfactual_policy_robustness.diagnostics import diagnostics
def rows(): return [LoggedOutcome('a','A',F(1),F(1,2),F(1,2),F(3,4)),LoggedOutcome('b','B',F(0),F(1,2),F(1,2),F(1,4)),LoggedOutcome('c','A',F(1),F(1,2),F(1,2),F(3,4))]
class TestEstimators(unittest.TestCase):
    def test_ips_snips_dr_and_ess(self):
        self.assertEqual(estimate(rows(),Estimator.IPS).value,F(2,3)); self.assertEqual(estimate(rows(),Estimator.SNIPS).value,F(2,3)); self.assertEqual(estimate(rows(),Estimator.DOUBLY_ROBUST).value,F(2,3)); self.assertEqual(diagnostics(rows()).ess,F(3))
