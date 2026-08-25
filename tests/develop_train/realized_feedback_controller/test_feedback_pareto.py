import unittest
from fractions import Fraction
from scripts.develop_train.realized_feedback_controller.health import Health,PolicyHealth
from scripts.develop_train.realized_feedback_controller.meta_policy import candidates
from scripts.develop_train.realized_feedback_controller.pareto import frontier
class TestFeedback(unittest.TestCase):
 def test_feedback_noncollapse_and_pareto(self):
  cs=candidates(PolicyHealth(Health.DRIFTED,"x"),bias=Fraction(1,2),regret=Fraction(1,2)); self.assertEqual(len({c.strategy for c in cs}),5); self.assertLessEqual(len(frontier(cs)),5); self.assertGreater(len(frontier(cs)),1)
