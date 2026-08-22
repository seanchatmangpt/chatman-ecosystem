import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.develop_train.evidence_acquisition_runtime.calibration import SensorCalibration
from scripts.develop_train.evidence_acquisition_runtime.subject import Refusal
class T(unittest.TestCase):
 def test_quality_support_and_freshness(self):
  n=datetime(2026,8,22,22,tzinfo=timezone.utc); SensorCalibration('a',2,20,Fraction(9,10),Fraction(1,10),n).admit(now=n)
  with self.assertRaisesRegex(Refusal,'INSUFFICIENT'): SensorCalibration('a',2,2,Fraction(9,10),Fraction(1,10),n).admit(now=n)
  with self.assertRaisesRegex(Refusal,'STALE'): SensorCalibration('a',2,20,Fraction(9,10),Fraction(1,10),n-timedelta(days=1)).admit(now=n)
  with self.assertRaisesRegex(Refusal,'UNRELIABLE'): SensorCalibration('a',2,20,Fraction(1,10),Fraction(2,10),n).admit(now=n)
