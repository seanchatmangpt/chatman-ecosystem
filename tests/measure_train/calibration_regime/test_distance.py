import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.calibration_regime.subject import Subject
from scripts.measure_train.calibration_regime.trial import CalibrationTrial
from scripts.measure_train.calibration_regime.window import CalibrationWindow
from scripts.measure_train.calibration_regime.model import fit_model
from scripts.measure_train.calibration_regime.distance import classify_distance,model_distance
class T(unittest.TestCase):
 def test_regime_distance(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject('o/r','a'*40)
  good=[CalibrationTrial(s,'x',True,True,t+timedelta(seconds=i)) for i in range(4)]
  bad=[CalibrationTrial(s,'x',True,False,t+timedelta(minutes=1,seconds=i)) for i in range(4)]
  a=fit_model(s,'x',CalibrationWindow(t,t+timedelta(minutes=1),4),good)
  b=fit_model(s,'x',CalibrationWindow(t+timedelta(minutes=1),t+timedelta(minutes=2),4),bad)
  self.assertEqual(classify_distance(a,b,Fraction(1,4)),'DRIFT'); self.assertGreater(model_distance(a,b).max_delta,0)
