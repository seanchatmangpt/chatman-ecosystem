import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.sequential_policy_msa.subject import Subject
from scripts.measure_train.sequential_policy_msa.policy import PolicyIdentity
from scripts.measure_train.sequential_policy_msa.step import StepObservation
from scripts.measure_train.sequential_policy_msa.change_detection import page_hinkley
class T(unittest.TestCase):
 def test_drift_signal(self):
  s=Subject("o/r","a"*40); p=PolicyIdentity("p",1,"1"*64,"MAX_INFORMATION"); now=datetime.now(timezone.utc)
  residuals=[0,0,0,2,2,2]
  rows=[StepObservation(s,p,i,f"e{i}",Fraction(1),Fraction(1+r),Fraction(0),Fraction(0),1,now,"PASS") for i,r in enumerate(residuals)]
  self.assertTrue(page_hinkley(rows,threshold=Fraction(1,2))["drift"])
