import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.calibration_regime.subject import Subject
from scripts.measure_train.calibration_regime.trial import CalibrationTrial
from scripts.measure_train.calibration_regime.cusum import detect_error_shift
class T(unittest.TestCase):
 def test_error_shift_crosses(self):
  t=datetime.now(timezone.utc); s=Subject('o/r','a'*40)
  rows=[CalibrationTrial(s,'x',True,False,t+timedelta(seconds=i)) for i in range(5)]
  r=detect_error_shift(rows,Fraction(1,10),Fraction(3,2),Fraction(0),4)
  self.assertEqual(r.state,'DRIFT'); self.assertIsNotNone(r.first_crossing)
