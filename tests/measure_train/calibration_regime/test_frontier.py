import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.calibration_regime.subject import Subject,Refused
from scripts.measure_train.calibration_regime.trial import CalibrationTrial
from scripts.measure_train.calibration_regime.window import CalibrationWindow
from scripts.measure_train.calibration_regime.model import fit_model
from scripts.measure_train.calibration_regime.frontier import ModelVersion,resolve_frontier
class T(unittest.TestCase):
 def test_divergent_max_generation_refuses(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject('o/r','a'*40)
  def model(start,pred):
   rows=[CalibrationTrial(s,'x',True,pred,start+timedelta(seconds=i)) for i in range(4)]
   return fit_model(s,'x',CalibrationWindow(start,start+timedelta(minutes=1),4),rows)
  with self.assertRaises(Refused): resolve_frontier([ModelVersion(2,model(t,True)),ModelVersion(2,model(t+timedelta(minutes=1),False))])
