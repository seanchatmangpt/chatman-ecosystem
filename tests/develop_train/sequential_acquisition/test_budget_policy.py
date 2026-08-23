import unittest
from fractions import Fraction
from scripts.develop_train.sequential_acquisition.budget import BudgetState
from scripts.develop_train.sequential_acquisition.policy import Candidate, select

class BudgetPolicyCourt(unittest.TestCase):
    def test_five_strategies_do_not_collapse(self):
        b=BudgetState(Fraction(10),Fraction(10),3)
        cs=[Candidate("info","s1",2.0,Fraction(1),Fraction(4),Fraction(4),0.1),Candidate("cheap","s2",1.2,Fraction(2),Fraction(1),Fraction(3),0.1),Candidate("ucb","s3",1.5,Fraction(1),Fraction(3),Fraction(1),1.0)]
        self.assertEqual(select(cs,b,"MAX_INFORMATION").candidate_id,"info")
        self.assertEqual(select(cs,b,"INFORMATION_PER_COST").candidate_id,"cheap")
        self.assertEqual(select(cs,b,"MAX_INDEPENDENCE").candidate_id,"cheap")
        self.assertEqual(select(cs,b,"UCB_DISCOVERY").candidate_id,"ucb")
        self.assertEqual(select(cs,b,"MINIMAX_LATENCY").candidate_id,"ucb")
