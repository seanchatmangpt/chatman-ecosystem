import unittest
from datetime import datetime,timezone
from scripts.measure_train.strategy_binding.subject import Subject,Refused
from scripts.measure_train.strategy_binding.cut import CutCandidate
from scripts.measure_train.strategy_binding.proof import SelectionProof
from scripts.measure_train.strategy_binding.receipt import manufacture_receipt
from scripts.measure_train.strategy_binding.replay import replay
class T(unittest.TestCase):
 def test_tamper(self):
  p=SelectionProof(Subject("c/r","a"*40),"c","1"*64,"2"*64,"p"); c=CutCandidate("c",1,(("o/a",1),),datetime.now(timezone.utc))
  r=manufacture_receipt(p,c,"PARTIAL_ALIVE"); self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["selected_cut_id"]="x"
  with self.assertRaises(Refused): replay(r)
