import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.sequential_policy_msa.subject import Subject
from scripts.measure_train.sequential_policy_msa.policy import PolicyIdentity
from scripts.measure_train.sequential_policy_msa.step import StepObservation
from scripts.measure_train.sequential_policy_msa.trajectory import admit_trajectory
class T(unittest.TestCase):
 def test_input_order_does_not_change_trajectory(self):
  s=Subject("o/r","a"*40); p=PolicyIdentity("p",1,"1"*64,"MAX_INFORMATION"); now=datetime.now(timezone.utc)
  rows=[StepObservation(s,p,i,f"e{i}",Fraction(1),Fraction(1),Fraction(0),Fraction(0),1,now+timedelta(seconds=i),"PASS") for i in range(3)]
  self.assertEqual(admit_trajectory(s,p,rows),admit_trajectory(s,p,list(reversed(rows))))
