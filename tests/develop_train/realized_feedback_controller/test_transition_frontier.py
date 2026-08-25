import unittest
from scripts.develop_train.realized_feedback_controller.errors import Refused
from scripts.develop_train.realized_feedback_controller.frontier import PolicyFrontier
from scripts.develop_train.realized_feedback_controller.policy import BaseStrategy,FeedbackStrategy,PolicyIdentity
from scripts.develop_train.realized_feedback_controller.transition import PolicyTransition
class TestTransition(unittest.TestCase):
 def test_current_frontier_and_monotonicity(self):
  p=PolicyIdentity("p",2,"a"*64,BaseStrategy.UCB_DISCOVERY); self.assertEqual(PolicyFrontier.current((p,)).generation,2); PolicyTransition(p,3,FeedbackStrategy.EXPLORE_DRIFT)
  with self.assertRaises(Refused): PolicyTransition(p,4,FeedbackStrategy.EXPLORE_DRIFT)
