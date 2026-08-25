import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.sequential_policy_msa.subject import Subject
from scripts.measure_train.sequential_policy_msa.policy import PolicyIdentity
from scripts.measure_train.sequential_policy_msa.step import StepObservation
from scripts.measure_train.sequential_policy_msa.calibration import forecast_calibration
class T(unittest.TestCase):
 def test_support_and_quality(self):
  s=Subject("o/r","a"*40); p=PolicyIdentity("p",1,"1"*64,"MAX_INFORMATION"); now=datetime.now(timezone.utc)
  rows=[StepObservation(s,p,i,f"e{i}",Fraction(1),Fraction(1),Fraction(0),Fraction(0),1,now,"PASS") for i in range(3)]
  self.assertEqual(forecast_calibration(rows)["state"],"CALIBRATED")
  self.assertEqual(forecast_calibration(rows[:2])["state"],"INSUFFICIENT")
