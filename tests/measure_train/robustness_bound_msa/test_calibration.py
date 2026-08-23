import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.robustness_bound_msa.subject import Subject
from scripts.measure_train.robustness_bound_msa.bound import RobustnessBound
from scripts.measure_train.robustness_bound_msa.case import BoundCase
from scripts.measure_train.robustness_bound_msa.calibration import calibrate
class T(unittest.TestCase):
 def test_support(self):
  s=Subject("o/r","a"*40); now=datetime.now(timezone.utc); b=RobustnessBound(Fraction(0),Fraction(1),Fraction(1),"IPS","a"*64)
  rows=[BoundCase(s,b,Fraction(1,2),str(i),now) for i in range(3)]
  self.assertEqual(calibrate(rows).state,"CALIBRATED")
