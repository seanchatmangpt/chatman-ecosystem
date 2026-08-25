import unittest
from fractions import Fraction as F
from scripts.develop_train.counterfactual_policy_robustness.receipt import Receipt,replay
from scripts.develop_train.counterfactual_policy_robustness.failure import FailureWorld
from scripts.develop_train.counterfactual_policy_robustness.evidence import LoggedOutcome
from scripts.develop_train.counterfactual_policy_robustness.authority import ActionClass,admit
from scripts.develop_train.counterfactual_policy_robustness.errors import Refused
class TestReceiptFailureAuthority(unittest.TestCase):
    def test_determinism_tamper_and_do_refusal(self):
        rows=[LoggedOutcome(str(i),'A',F(i%2),F(1,2),F(1,2)) for i in range(20)]; self.assertEqual(FailureWorld('s').apply(rows),FailureWorld('s').apply(reversed(rows))); r=Receipt('x',1,'p','MAX_LOWER','PARTIAL_ALIVE'); self.assertEqual(replay(r,r.digest()),'REPLAY_MATCH')
        with self.assertRaisesRegex(Refused,'TAMPER'): replay(r,'0'*64)
        with self.assertRaisesRegex(Refused,'BRCE'): admit(ActionClass.DO)
