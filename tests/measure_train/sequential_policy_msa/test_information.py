import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.sequential_policy_msa.subject import Subject
from scripts.measure_train.sequential_policy_msa.policy import PolicyIdentity
from scripts.measure_train.sequential_policy_msa.step import StepObservation
from scripts.measure_train.sequential_policy_msa.information import cumulative_information,trajectory_entropy
class T(unittest.TestCase):
 def test_information(self):
  s=Subject("o/r","a"*40); p=PolicyIdentity("p",1,"1"*64,"MAX_INFORMATION"); now=datetime.now(timezone.utc)
  r=StepObservation(s,p,0,"e",Fraction(1),Fraction(3,2),Fraction(1),Fraction(1),1,now,"PASS")
  self.assertEqual(cumulative_information([r])[2],Fraction(1,2))
  self.assertAlmostEqual(trajectory_entropy([1,1]),1.0)
