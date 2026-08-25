import unittest
from scripts.measure_train.cross_control_msa.calibration import calibrate
from scripts.measure_train.cross_control_msa.subject import Subject
from scripts.measure_train.cross_control_msa.receipt import manufacture
from scripts.measure_train.cross_control_msa.replay import replay
from scripts.measure_train.cross_control_msa.refusal import Refused
class T(unittest.TestCase):
 def test_calibration_and_tamper(self):
  self.assertEqual(calibrate([1,1,0,1,0],[1,0,0,1,0]).state,"CALIBRATED")
  r=manufacture(Subject("o/r","a"*40,"b"*64,1),"c"*64,4,"PARTIAL_ALIVE");self.assertEqual(replay(r),"REPLAY_MATCH");r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
