import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.calibration_regime.subject import Subject,Refused
from scripts.measure_train.calibration_regime.trial import CalibrationTrial
from scripts.measure_train.calibration_regime.window import CalibrationWindow
from scripts.measure_train.calibration_regime.model import fit_model
from scripts.measure_train.calibration_regime.frontier import ModelVersion
from scripts.measure_train.calibration_regime.qualify import qualify
from scripts.measure_train.calibration_regime.replay import replay
class T(unittest.TestCase):
 def test_stable_then_regime_shift_invalidates_current_calibration(self):
  t=datetime(2026,8,22,tzinfo=timezone.utc); s=Subject('o/r','a'*40)
  def model(start,pred):
   rows=[CalibrationTrial(s,'source-a',True,pred,start+timedelta(seconds=i)) for i in range(6)]
   return fit_model(s,'source-a',CalibrationWindow(start,start+timedelta(minutes=1),4),rows)
  ref=model(t,True); stable=model(t+timedelta(minutes=1),True)
  q=qualify(s,'source-a',ref,[ModelVersion(1,stable)],['PASS'],t+timedelta(minutes=3),Fraction(1,4))
  self.assertEqual(q['standing'],'PARTIAL_ALIVE'); self.assertEqual(q['drift_state'],'STABLE'); self.assertEqual(replay(q['receipt']),'REPLAY_MATCH'); self.assertFalse(q['actuation_performed'])
  drifted=model(t+timedelta(minutes=2),False)
  with self.assertRaisesRegex(Refused,'CALIBRATION_DRIFTED'):
   qualify(s,'source-a',ref,[ModelVersion(2,drifted)],['PASS'],t+timedelta(minutes=4),Fraction(1,4))
