import unittest
from fractions import Fraction
from datetime import datetime,timezone,timedelta
from scripts.measure_train.evidence_voi.candidate import MeasurementCandidate
from scripts.measure_train.evidence_voi.calibration import SensorCalibration,admit_calibration
from scripts.measure_train.evidence_voi.subject import Refused
class T(unittest.TestCase):
 def test_support_and_staleness(self):
  now=datetime.now(timezone.utc); c=MeasurementCandidate("a","f","d","REPOSITORY",Fraction(1),1)
  low=SensorCalibration("a",1,2,Fraction(9,10),Fraction(1,10),now)
  with self.assertRaises(Refused): admit_calibration(c,low,now)
  stale=SensorCalibration("a",1,10,Fraction(9,10),Fraction(1,10),now-timedelta(hours=2))
  with self.assertRaises(Refused): admit_calibration(c,stale,now)
