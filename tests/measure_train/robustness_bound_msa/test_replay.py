import unittest
from scripts.measure_train.robustness_bound_msa.subject import Subject,Refused
from scripts.measure_train.robustness_bound_msa.frontier import CalibrationModel
from scripts.measure_train.robustness_bound_msa.receipt import manufacture
from scripts.measure_train.robustness_bound_msa.replay import replay
class T(unittest.TestCase):
 def test_tamper(self):
  r=manufacture(Subject("o/r","a"*40),(CalibrationModel("IPS",1,"a"*64,"CALIBRATED"),),"PARTIAL_ALIVE")
  self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
