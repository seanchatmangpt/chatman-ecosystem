import unittest
from fractions import Fraction as F
from scripts.develop_train.counterfactual_policy_robustness import *
from scripts.develop_train.counterfactual_policy_robustness.receipt import replay
class TestChicago(unittest.TestCase):
    def test_end_to_end_bounded_transition_evidence(self):
        subject=Subject('seanchatmangpt/chatman-ecosystem@'+'3'*40); policy=PolicyIdentity(7,'d'*64,PolicyFamily.CURRENT); rows=[LoggedOutcome('a','A',F(1),F(1,2),F(1,2),F(3,4)),LoggedOutcome('b','B',F(0),F(1,2),F(1,2),F(1,4)),LoggedOutcome('c','A',F(1),F(1,2),F(1,2),F(3,4))]; ev=RobustPolicyEngine().evaluate(subject,policy,rows,[Calibration(2,'cal',8,F(1,20))],F(3,2),RobustStrategy.MAX_LOWER); self.assertEqual(ev.standing,'PARTIAL_ALIVE'); self.assertFalse(ev.receipt.actuation_performed); self.assertEqual(replay(ev.receipt,ev.receipt.digest()),'REPLAY_MATCH')
