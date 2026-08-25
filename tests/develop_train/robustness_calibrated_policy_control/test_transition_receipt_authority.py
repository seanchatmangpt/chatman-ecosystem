import unittest
from scripts.develop_train.robustness_calibrated_policy_control.transition import PortfolioTransition
from scripts.develop_train.robustness_calibrated_policy_control.receipt import Receipt,replay
from scripts.develop_train.robustness_calibrated_policy_control.authority import ActionClass,admit
from scripts.develop_train.robustness_calibrated_policy_control.refusal import Refused
class T(unittest.TestCase):
 def test_transition_receipt_and_do(self):
  PortfolioTransition(2,3,('a',))
  with self.assertRaises(Refused): PortfolioTransition(2,4,('a',))
  r=Receipt('o/r@'+'a'*40,2,'MAX_LOWER',('a',),'PARTIAL_ALIVE'); self.assertTrue(replay(r,r.digest())); self.assertFalse(replay(r,'0'*64))
  with self.assertRaises(Refused): admit(ActionClass.DO)
