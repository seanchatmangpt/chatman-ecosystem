import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.develop_train.realized_feedback_controller.authority import ActionClass,admit_action
from scripts.develop_train.realized_feedback_controller.errors import Refused
from scripts.develop_train.realized_feedback_controller.failure import FailureWorld
from scripts.develop_train.realized_feedback_controller.realization import StepRealization
from scripts.develop_train.realized_feedback_controller.receipt import Receipt,replay
class TestSafety(unittest.TestCase):
 def test_deterministic_failure_receipt_do(self):
  s=StepRealization(0,"e",1,1,1,1,1,datetime.now(timezone.utc)); w=FailureWorld("seed",Fraction(1,10),2); self.assertEqual(w.apply(s),w.apply(s)); r=Receipt("o/r@"+"a"*40,1,"HOLD","PARTIAL_ALIVE"); self.assertTrue(replay(r,r.digest())); self.assertFalse(replay(r,"0"*64))
  with self.assertRaises(Refused): admit_action(ActionClass.DO)
