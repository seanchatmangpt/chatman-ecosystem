import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.develop_train.realized_feedback_controller.budget import FeedbackBudget
from scripts.develop_train.realized_feedback_controller.engine import FeedbackEngine
from scripts.develop_train.realized_feedback_controller.policy import BaseStrategy,FeedbackStrategy,PolicyIdentity
from scripts.develop_train.realized_feedback_controller.realization import StepRealization
from scripts.develop_train.realized_feedback_controller.receipt import replay
from scripts.develop_train.realized_feedback_controller.standing import Standing
from scripts.develop_train.realized_feedback_controller.subject import Subject
from scripts.develop_train.realized_feedback_controller.trajectory import Trajectory
class TestChicago(unittest.TestCase):
 def test_closed_loop_feedback_without_do(self):
  t=datetime.now(timezone.utc); subject=Subject("o/r@"+"c"*40); policy=PolicyIdentity("policy",4,"d"*64,BaseStrategy.MAX_INFORMATION)
  healthy=Trajectory(tuple(StepRealization(i,f"h{i}",Fraction(1,2),Fraction(1,2),1,1,1,t) for i in range(3)))
  ev=FeedbackEngine().evaluate(subject,policy,healthy); self.assertEqual(ev.selected,FeedbackStrategy.HOLD); self.assertEqual(ev.standing,Standing.PARTIAL_ALIVE); self.assertIsNone(ev.transition); self.assertTrue(replay(ev.receipt,ev.receipt.digest()))
  biased=Trajectory(tuple(StepRealization(i,f"b{i}",1,Fraction(1,4),1,1,1,t) for i in range(3)))
  ev2=FeedbackEngine().evaluate(subject,policy,biased,regret=Fraction(1,2),budget=FeedbackBudget(2,1)); self.assertEqual(ev2.standing,Standing.UNKNOWN); self.assertIsNotNone(ev2.transition); self.assertFalse(ev2.receipt.actuation_performed)
