import unittest
from datetime import datetime,timezone
from scripts.measure_train.evidence_calibration.subject import Subject
from scripts.measure_train.evidence_calibration.admission import CurrentWitness
from scripts.measure_train.evidence_calibration.calibration import CalibrationEstimate
from scripts.measure_train.evidence_calibration.sequential import sequential_test
class T(unittest.TestCase):
 def test_accept_and_fail_dominance(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40); e=CalibrationEstimate("x",20,.9,.1,.1,.5)
  w=CurrentWitness(s,"c","x","PASS",now,"a")
  self.assertEqual(sequential_test([w],[e],1,-1).decision,"ACCEPT_BOUNDED")
