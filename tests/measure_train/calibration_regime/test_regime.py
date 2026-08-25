import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.calibration_regime.subject import Subject
from scripts.measure_train.calibration_regime.trial import CalibrationTrial
from scripts.measure_train.calibration_regime.window import CalibrationWindow
from scripts.measure_train.calibration_regime.model import fit_model
from scripts.measure_train.calibration_regime.regime import segment_models
class T(unittest.TestCase):
 def test_generation_advances_on_drift(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject('o/r','a'*40)
  def model(start, correct):
   rows=[CalibrationTrial(s,'x',True,correct,start+timedelta(seconds=i)) for i in range(4)]
   return fit_model(s,'x',CalibrationWindow(start,start+timedelta(minutes=1),4),rows)
  r=segment_models([model(t,True),model(t+timedelta(minutes=1),False)],Fraction(1,4))
  self.assertEqual(r[-1].generation,1); self.assertEqual(r[-1].state,'DRIFT')
