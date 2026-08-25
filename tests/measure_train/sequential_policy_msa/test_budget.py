import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.sequential_policy_msa.subject import Subject
from scripts.measure_train.sequential_policy_msa.policy import PolicyIdentity
from scripts.measure_train.sequential_policy_msa.step import StepObservation
from scripts.measure_train.sequential_policy_msa.budget import Budget,budget_state
class T(unittest.TestCase):
 def test_escape(self):
  s=Subject("o/r","a"*40); p=PolicyIdentity("p",1,"1"*64,"MAX_INFORMATION"); now=datetime.now(timezone.utc)
  r=StepObservation(s,p,0,"e",Fraction(1),Fraction(1),Fraction(2),Fraction(1),1,now,"PASS")
  self.assertTrue(budget_state([r],Budget(Fraction(1),Fraction(5),2,2))["exhausted"])
