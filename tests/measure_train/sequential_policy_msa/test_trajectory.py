import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.sequential_policy_msa.subject import Subject
from scripts.measure_train.sequential_policy_msa.policy import PolicyIdentity
from scripts.measure_train.sequential_policy_msa.step import StepObservation
from scripts.measure_train.sequential_policy_msa.trajectory import admit_trajectory
from scripts.measure_train.sequential_policy_msa.refusal import Refused
class T(unittest.TestCase):
 def test_gap_refuses(self):
  s=Subject("o/r","a"*40); p=PolicyIdentity("p",1,"1"*64,"MAX_INFORMATION"); now=datetime.now(timezone.utc)
  row=StepObservation(s,p,1,"e",Fraction(1),Fraction(1),Fraction(1),Fraction(1),1,now,"PASS")
  with self.assertRaises(Refused): admit_trajectory(s,p,[row])
