import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.calibration_cohort.subject import Subject
from scripts.measure_train.calibration_cohort.schema import CalibrationSchema
from scripts.measure_train.calibration_cohort.interval import Interval
from scripts.measure_train.calibration_cohort.epoch import CalibrationEpoch
from scripts.measure_train.calibration_cohort.cohort import CalibrationCohort
from scripts.measure_train.calibration_cohort.observation import Observation
from scripts.measure_train.calibration_cohort.census import census
class T(unittest.TestCase):
 def test_fail_dominates(self):
  n=datetime.now(timezone.utc); e=CalibrationEpoch("x",Subject("o/x","a"*40),1,"1"*64,CalibrationSchema("t","d","f"),Interval(n,n+timedelta(seconds=1)),2,"STABLE")
  c=CalibrationCohort((e,),frozenset({"x"})); obs=[Observation("x",1,"PASS","a",n),Observation("x",1,"FAIL","b",n)]
  self.assertEqual(census(c,obs),(("x","FAIL"),))
