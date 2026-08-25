import unittest
from scripts.measure_train.evidence_calibration.subject import Subject,Refused
from scripts.measure_train.evidence_calibration.sequential import SequentialResult
from scripts.measure_train.evidence_calibration.receipt import manufacture_receipt
from scripts.measure_train.evidence_calibration.replay import replay
class T(unittest.TestCase):
 def test_replay_tamper(self):
  r=manufacture_receipt(Subject("o/r","a"*40),(),SequentialResult(0,"CONTINUE",()),"UNKNOWN",())
  self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["standing"]="PARTIAL_ALIVE"
  with self.assertRaises(Refused): replay(r)
