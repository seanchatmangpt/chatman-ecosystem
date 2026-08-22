import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.calibration_regime.subject import Subject
from scripts.measure_train.calibration_regime.trial import CalibrationTrial
from scripts.measure_train.calibration_regime.window import CalibrationWindow
class T(unittest.TestCase):
 def test_half_open_boundary(self):
  start=datetime(2026,8,22,tzinfo=timezone.utc); end=start+timedelta(hours=1); s=Subject('o/r','a'*40)
  rows=[CalibrationTrial(s,'x',True,True,start),CalibrationTrial(s,'x',True,True,end)]
  self.assertEqual(len(CalibrationWindow(start,end,1).select(rows)),1)
