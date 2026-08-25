import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.calibration_regime.subject import Subject,Refused
from scripts.measure_train.calibration_regime.trial import CalibrationTrial
from scripts.measure_train.calibration_regime.window import CalibrationWindow
from scripts.measure_train.calibration_regime.model import fit_model
from scripts.measure_train.calibration_regime.distance import DriftVector
from scripts.measure_train.calibration_regime.receipt import manufacture_receipt
from scripts.measure_train.calibration_regime.replay import replay
class T(unittest.TestCase):
 def test_deterministic_tamper_sensitive_no_do(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject('o/r','a'*40)
  rows=[CalibrationTrial(s,'x',True,True,t+timedelta(seconds=i)) for i in range(4)]
  m=fit_model(s,'x',CalibrationWindow(t,t+timedelta(minutes=1),4),rows); d=DriftVector(Fraction(0),Fraction(0),Fraction(0))
  a=manufacture_receipt(s,'x',m,0,d,'STABLE','PARTIAL_ALIVE'); b=manufacture_receipt(s,'x',m,0,d,'STABLE','PARTIAL_ALIVE')
  self.assertEqual(a,b); self.assertFalse(a['body']['actuation_performed']); self.assertEqual(replay(a),'REPLAY_MATCH')
  a['body']['standing']='ALIVE'
  with self.assertRaises(Refused): replay(a)
