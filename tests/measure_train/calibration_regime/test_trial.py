import unittest
from datetime import datetime,timezone
from scripts.measure_train.calibration_regime.subject import Subject,Refused
from scripts.measure_train.calibration_regime.trial import CalibrationTrial,admit_trials
class T(unittest.TestCase):
 def test_duplicate_and_foreign_refuse(self):
  s=Subject('o/r','a'*40); now=datetime.now(timezone.utc); t=CalibrationTrial(s,'src',True,True,now)
  with self.assertRaises(Refused): admit_trials(s,'src',[t,t])
  with self.assertRaises(Refused): CalibrationTrial(s,'src',True,True,datetime.now())
