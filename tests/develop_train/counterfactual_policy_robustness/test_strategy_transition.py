import unittest
from fractions import Fraction as F
from scripts.develop_train.counterfactual_policy_robustness.sensitivity import Interval
from scripts.develop_train.counterfactual_policy_robustness.intervals import CandidateInterval,pareto
from scripts.develop_train.counterfactual_policy_robustness.strategies import RobustStrategy,select
from scripts.develop_train.counterfactual_policy_robustness.policy import PolicyIdentity,PolicyFamily
from scripts.develop_train.counterfactual_policy_robustness.transition import PolicyTransition
from scripts.develop_train.counterfactual_policy_robustness.errors import Refused
class TestStrategyTransition(unittest.TestCase):
    def test_pareto_strategy_noncollapse_and_generation(self):
        a=CandidateInterval('a',Interval(F(1,2),F(4,5)),F(2)); b=CandidateInterval('b',Interval(F(2,5),F(1,2)),F(3)); front=pareto([a,b]); self.assertEqual(len(front),2); self.assertNotEqual(select(front,RobustStrategy.MAX_LOWER).policy_digest,select(front,RobustStrategy.MIN_WIDTH).policy_digest); p=PolicyIdentity(3,'a'*64,PolicyFamily.CURRENT); q=PolicyIdentity(4,'b'*64,PolicyFamily.LOWER_BOUND); self.assertEqual(PolicyTransition(p,q,RobustStrategy.MAX_LOWER).after.generation,4)
        with self.assertRaisesRegex(Refused,'NON_MONOTONE'): PolicyTransition(p,PolicyIdentity(5,'c'*64,PolicyFamily.LOWER_BOUND),RobustStrategy.MAX_LOWER)
