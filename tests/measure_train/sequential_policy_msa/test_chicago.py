import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.sequential_policy_msa.subject import Subject
from scripts.measure_train.sequential_policy_msa.policy import PolicyIdentity
from scripts.measure_train.sequential_policy_msa.step import StepObservation
from scripts.measure_train.sequential_policy_msa.budget import Budget
from scripts.measure_train.sequential_policy_msa.qualify import qualify
from scripts.measure_train.sequential_policy_msa.receipt import replay
class T(unittest.TestCase):
 def test_end_to_end_bounded_policy_msa(self):
  s=Subject("o/r","a"*40); p=PolicyIdentity("seq",4,"1"*64,"UCB_DISCOVERY"); now=datetime.now(timezone.utc)
  rows=[StepObservation(s,p,i,f"e{i}",Fraction(1),Fraction(1),Fraction(1),Fraction(10),1,now+timedelta(seconds=i),"PASS") for i in range(3)]
  q=qualify(s,p,rows,p,now+timedelta(seconds=5),Budget(Fraction(5),Fraction(100),5,5))
  self.assertEqual(q["standing"],"PARTIAL_ALIVE")
  self.assertFalse(q["actuation_performed"])
  self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
