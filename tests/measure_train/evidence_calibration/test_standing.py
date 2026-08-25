import unittest
from datetime import datetime,timezone
from scripts.measure_train.evidence_calibration.subject import Subject
from scripts.measure_train.evidence_calibration.admission import CurrentWitness
from scripts.measure_train.evidence_calibration.sequential import SequentialResult
from scripts.measure_train.evidence_calibration.standing import standing
class T(unittest.TestCase):
 def test_under_calibrated_stays_unknown(self):
  s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
  ws=[CurrentWitness(s,"a","x","PASS",now,"1"),CurrentWitness(s,"b","y","PASS",now,"2")]
  self.assertEqual(standing(ws,("x",),SequentialResult(9,"ACCEPT_BOUNDED",()),2),"UNKNOWN")
