import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.calibration_cohort.subject import Subject,Refused
from scripts.measure_train.calibration_cohort.schema import CalibrationSchema
from scripts.measure_train.calibration_cohort.interval import Interval
from scripts.measure_train.calibration_cohort.epoch import CalibrationEpoch
from scripts.measure_train.calibration_cohort.cohort import CalibrationCohort
from scripts.measure_train.calibration_cohort.admission import admit_cohort
class T(unittest.TestCase):
 def test_schema_and_currentness(self):
  n=datetime.now(timezone.utc); w=Interval(n,n+timedelta(seconds=10)); a=Subject("o/a","a"*40)
  s1=CalibrationSchema("t","d","f"); s2=CalibrationSchema("other","d","f")
  x=CalibrationEpoch("x",a,1,"1"*64,s1,w,10,"STABLE"); y=CalibrationEpoch("y",Subject("o/b","b"*40),1,"2"*64,s2,w,10,"STABLE")
  with self.assertRaises(Refused): admit_cohort(CalibrationCohort((x,y),frozenset({"x","y"})),(x,y))
