import unittest
from datetime import datetime,timezone
from scripts.measure_train.evidence_calibration.subject import Subject
from scripts.measure_train.evidence_calibration.admission import CurrentWitness
from scripts.measure_train.evidence_calibration.sequential import SequentialResult
from scripts.measure_train.evidence_calibration.telemetry import project
class T(unittest.TestCase):
 def test_exact_subject(self):
  s=Subject("o/r","a"*40); w=CurrentWitness(s,"c","x","PASS",datetime.now(timezone.utc),"e")
  self.assertEqual(project(s,[w],[],SequentialResult(0,"CONTINUE",()))[0]["sha"],s.sha)
