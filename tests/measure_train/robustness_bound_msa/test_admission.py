import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.robustness_bound_msa.subject import Subject,Refused
from scripts.measure_train.robustness_bound_msa.bound import RobustnessBound
from scripts.measure_train.robustness_bound_msa.case import BoundCase
from scripts.measure_train.robustness_bound_msa.frontier import CalibrationModel
from scripts.measure_train.robustness_bound_msa.admission import admit_case
class T(unittest.TestCase):
 def test_width_refusal(self):
  s=Subject("o/r","a"*40); now=datetime.now(timezone.utc); b=RobustnessBound(Fraction(0),Fraction(1),Fraction(1),"IPS","a"*64)
  c=BoundCase(s,b,Fraction(1,2),"e",now)
  with self.assertRaises(Refused): admit_case(s,c,CalibrationModel("IPS",1,"b"*64,"CALIBRATED"),now,max_width=Fraction(1,2))
