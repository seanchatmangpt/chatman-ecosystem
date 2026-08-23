import unittest
from datetime import datetime, timezone, timedelta
from fractions import Fraction
from scripts.develop_train.fused_acquisition.calibration import Calibration
from scripts.develop_train.fused_acquisition.sensor import Sensor,Observation
from scripts.develop_train.fused_acquisition.refusals import Refused
class TestCalibrationSensor(unittest.TestCase):
 def test_calibration_and_observation_identity(self):
  c=Calibration(2,'1'*64,20,Fraction(1,20),Fraction(1,20),Fraction(1,20)); self.assertEqual(c.error_mass,Fraction(3,20))
  Sensor('s1','fam1','dom1',c)
  Observation('s1',2,'CURRENT',Fraction(4,5),datetime.now(timezone.utc)-timedelta(seconds=1))
  with self.assertRaises(Refused): Observation('s1',2,'BAD',Fraction(1,2),datetime.now(timezone.utc))
