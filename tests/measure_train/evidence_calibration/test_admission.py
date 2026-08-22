import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.evidence_calibration.subject import Subject,Refused
from scripts.measure_train.evidence_calibration.admission import CurrentWitness,admit
from scripts.measure_train.evidence_calibration.calibration import CalibrationEstimate
class T(unittest.TestCase):
 def test_future_foreign(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40)
  e=CalibrationEstimate("x",10,.9,.1,.1,.5)
  w=CurrentWitness(s,"c","x","PASS",now+timedelta(seconds=1),"e")
  with self.assertRaises(Refused): admit(s,[w],[e],now,4)
