import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.calibration_cohort.subject import Subject,Refused
from scripts.measure_train.calibration_cohort.schema import CalibrationSchema
from scripts.measure_train.calibration_cohort.interval import Interval
from scripts.measure_train.calibration_cohort.epoch import CalibrationEpoch
from scripts.measure_train.calibration_cohort.cohort import CalibrationCohort
class T(unittest.TestCase):
 def test_required_sources_exact(self):
  n=datetime.now(timezone.utc); e=CalibrationEpoch("x",Subject("o/r","a"*40),1,"1"*64,CalibrationSchema("t","d","f"),Interval(n,n+timedelta(seconds=1)),1,"STABLE")
  self.assertEqual(CalibrationCohort((e,),frozenset({"x"})).by_source()["x"],e)
  with self.assertRaises(Refused): CalibrationCohort((e,),frozenset({"x","y"}))
