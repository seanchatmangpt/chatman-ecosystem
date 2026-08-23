import unittest
from scripts.measure_train.counterfactual_evaluator_msa.subject import Subject
from scripts.measure_train.counterfactual_evaluator_msa.receipt import manufacture_receipt
from scripts.measure_train.counterfactual_evaluator_msa.replay import replay
from scripts.measure_train.counterfactual_evaluator_msa.refusal import Refused
class T(unittest.TestCase):
 def test_tamper_no_do(self):
  r=manufacture_receipt(Subject("o/r","a"*40),"f"*64,{"state":"COHERENT","center":0,"mad":0},[],"PARTIAL_ALIVE")
  self.assertEqual(replay(r),"REPLAY_MATCH"); self.assertFalse(r["body"]["actuation_performed"])
  r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
