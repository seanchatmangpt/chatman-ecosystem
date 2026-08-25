import unittest
from datetime import datetime,timezone
from scripts.measure_train.evidence_calibration.trial import CalibrationTrial
from scripts.measure_train.evidence_calibration.subject import Refused
class T(unittest.TestCase):
 def test_time(self):
  self.assertTrue(CalibrationTrial("s","t",True,True,datetime.now(timezone.utc)).truth_positive)
  with self.assertRaises(Refused): CalibrationTrial("s","t2",True,True,datetime.now())
