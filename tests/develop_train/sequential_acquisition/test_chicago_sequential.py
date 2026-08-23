import unittest
from datetime import datetime, timezone
from fractions import Fraction
from scripts.develop_train.sequential_acquisition.belief import BeliefState
from scripts.develop_train.sequential_acquisition.budget import BudgetState
from scripts.develop_train.sequential_acquisition.evidence import ObservationEvidence
from scripts.develop_train.sequential_acquisition.engine import advance, plan_next
from scripts.develop_train.sequential_acquisition.policy import Candidate
from scripts.develop_train.sequential_acquisition.receipt import replay
from scripts.develop_train.sequential_acquisition.stopping import StopRule
from scripts.develop_train.sequential_acquisition.subject import Subject

class ChicagoSequentialCourt(unittest.TestCase):
    def test_observe_update_consume_select_stop_without_actuation(self):
        s=Subject("seanchatmangpt/chatman-ecosystem@"+"c"*40)
        prior=BeliefState(0,{"current":Fraction(1,2),"stale":Fraction(1,2)})
        budget=BudgetState(Fraction(5),Fraction(5),2)
        evidence=ObservationEvidence("sensor-a","obs-1",datetime.now(timezone.utc),{"current":Fraction(4,5),"stale":Fraction(1,5)},Fraction(1),Fraction(1))
        t=advance(s,prior,budget,evidence,predicted_bits=0.25,step=1)
        self.assertEqual(t.belief.probabilities["current"],Fraction(4,5))
        self.assertEqual(t.budget.samples_remaining,1)
        self.assertTrue(replay(t.receipt,t.receipt.digest()))
        candidates=[Candidate("probe-b","b",0.4,Fraction(1),Fraction(1),Fraction(1),0.2)]
        next_receipt=plan_next(s,t.belief,t.budget,candidates,"UCB_DISCOVERY",StopRule(Fraction(9,10),3),2)
        self.assertEqual(next_receipt.selected_candidate,"probe-b")
        stop_receipt=plan_next(s,BeliefState(2,{"current":Fraction(19,20),"stale":Fraction(1,20)}),t.budget,candidates,"MAX_INFORMATION",StopRule(Fraction(9,10),3),3)
        self.assertIsNone(stop_receipt.selected_candidate)
        self.assertFalse(stop_receipt.actuation_performed)
