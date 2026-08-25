import unittest
from scripts.develop_train.realized_feedback_controller.errors import Refused
from scripts.develop_train.realized_feedback_controller.policy import BaseStrategy, PolicyIdentity
from scripts.develop_train.realized_feedback_controller.subject import Subject
class TestIdentity(unittest.TestCase):
 def test_exact_subject_and_policy(self):
  Subject("o/r@"+"a"*40); PolicyIdentity("p",1,"b"*64,BaseStrategy.MAX_INFORMATION)
  with self.assertRaises(Refused): Subject("o/r@short")
