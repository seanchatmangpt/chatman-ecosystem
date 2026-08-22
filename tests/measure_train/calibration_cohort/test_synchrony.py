import unittest
from datetime import datetime,timezone,timedelta
from fractions import Fraction
from scripts.measure_train.calibration_cohort.subject import Subject
from scripts.measure_train.calibration_cohort.schema import CalibrationSchema
from scripts.measure_train.calibration_cohort.interval import Interval
from scripts.measure_train.calibration_cohort.epoch import CalibrationEpoch
from scripts.measure_train.calibration_cohort.synchrony import measure_synchrony
class T(unittest.TestCase):
 def test_exact_temporal_geometry(self):
  n=datetime.now(timezone.utc); s=CalibrationSchema("t","d","f")
  a=CalibrationEpoch("a",Subject("o/a","a"*40),1,"1"*64,s,Interval(n,n+timedelta(seconds=10)),10,"STABLE")
  b=CalibrationEpoch("b",Subject("o/b","b"*40),1,"2"*64,s,Interval(n+timedelta(seconds=2),n+timedelta(seconds=10)),10,"STABLE")
  self.assertEqual(measure_synchrony([a,b]).overlap,Fraction(4,5))
