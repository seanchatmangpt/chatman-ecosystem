import unittest
from scripts.measure_train.validation_independence_realization_msa.subject import Subject,Refused
from scripts.measure_train.validation_independence_realization_msa.frontier import IndependenceModel
from scripts.measure_train.validation_independence_realization_msa.receipt import manufacture
from scripts.measure_train.validation_independence_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_tamper_refuses(self):
  r=manufacture(Subject("o/r","a"*40,"b"*64),IndependenceModel(1,"c"*64,"CALIBRATED"),{"support":10},"PARTIAL_ALIVE")
  self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
