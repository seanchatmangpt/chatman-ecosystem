import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.sequential_policy_msa.subject import Subject
from scripts.measure_train.sequential_policy_msa.policy import PolicyIdentity
from scripts.measure_train.sequential_policy_msa.step import StepObservation
from scripts.measure_train.sequential_policy_msa.standing import standing
class T(unittest.TestCase):
 def test_ceiling_and_blocker(self):
  s=Subject("o/r","a"*40); p=PolicyIdentity("p",1,"1"*64,"MAX_INFORMATION"); now=datetime.now(timezone.utc)
  row=StepObservation(s,p,0,"e",Fraction(1),Fraction(1),Fraction(0),Fraction(0),1,now,"PASS")
  b={"exhausted":False}
  self.assertEqual(standing([row],b,"CALIBRATED"),"PARTIAL_ALIVE")
  self.assertEqual(standing([row],b,"CALIBRATED",["BUILD_BROKEN"]),"BLOCKED")
