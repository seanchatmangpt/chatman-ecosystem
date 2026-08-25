import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.calibration_regime.subject import Subject
from scripts.measure_train.calibration_regime.trial import CalibrationTrial
from scripts.measure_train.calibration_regime.window import CalibrationWindow
from scripts.measure_train.calibration_regime.model import fit_model
class T(unittest.TestCase):
 def test_exact_rates(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject('o/r','a'*40)
  vals=[(1,1),(1,1),(0,0),(0,1)]
  rows=[CalibrationTrial(s,'x',bool(a),bool(b),t+timedelta(seconds=i)) for i,(a,b) in enumerate(vals)]
  m=fit_model(s,'x',CalibrationWindow(t,t+timedelta(minutes=1),4),rows)
  self.assertEqual(m.support,4); self.assertEqual(m.brier,Fraction(1,4)); self.assertEqual(m.tpr,Fraction(3,4))
