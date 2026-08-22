import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.calibration_cohort.subject import Subject
from scripts.measure_train.calibration_cohort.schema import CalibrationSchema
from scripts.measure_train.calibration_cohort.interval import Interval
from scripts.measure_train.calibration_cohort.epoch import CalibrationEpoch
from scripts.measure_train.calibration_cohort.frontier import current_frontier
class T(unittest.TestCase):
 def test_latest_generation(self):
  n=datetime.now(timezone.utc); s=CalibrationSchema("t","d","f"); sub=Subject("o/r","a"*40); w=Interval(n,n+timedelta(seconds=1))
  a=CalibrationEpoch("x",sub,1,"1"*64,s,w,5,"STABLE"); b=CalibrationEpoch("x",sub,2,"2"*64,s,w,5,"STABLE")
  self.assertEqual(current_frontier([a,b])[0],b)
