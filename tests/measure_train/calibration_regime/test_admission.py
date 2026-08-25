import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.calibration_regime.subject import Subject,Refused
from scripts.measure_train.calibration_regime.trial import CalibrationTrial
from scripts.measure_train.calibration_regime.window import CalibrationWindow
from scripts.measure_train.calibration_regime.model import fit_model
from scripts.measure_train.calibration_regime.frontier import ModelVersion,resolve_frontier
from scripts.measure_train.calibration_regime.admission import admit_current_model
class T(unittest.TestCase):
 def test_currentness_guards(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject('o/r','a'*40)
  rows1=[CalibrationTrial(s,'x',True,True,t+timedelta(seconds=i)) for i in range(4)]
  rows2=[CalibrationTrial(s,'x',True,True,t+timedelta(minutes=1,seconds=i)) for i in range(4)]
  old=fit_model(s,'x',CalibrationWindow(t,t+timedelta(minutes=1),4),rows1)
  new=fit_model(s,'x',CalibrationWindow(t+timedelta(minutes=1),t+timedelta(minutes=2),4),rows2)
  frontier=resolve_frontier([ModelVersion(0,old),ModelVersion(1,new)])
  with self.assertRaises(Refused): admit_current_model(old,frontier,'STABLE',t+timedelta(minutes=3))
  with self.assertRaises(Refused): admit_current_model(new,frontier,'DRIFT',t+timedelta(minutes=3))
