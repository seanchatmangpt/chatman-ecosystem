import unittest
from datetime import datetime,timezone
from scripts.measure_train.strategy_binding.subject import Subject
from scripts.measure_train.strategy_binding.cut import CutCandidate
from scripts.measure_train.strategy_binding.proof import SelectionProof
from scripts.measure_train.strategy_binding.receipt import manufacture_receipt
class T(unittest.TestCase):
 def test_deterministic_no_do(self):
  p=SelectionProof(Subject("c/r","a"*40),"c","1"*64,"2"*64,"p")
  c=CutCandidate("c",1,(("o/a",1),),datetime(2026,8,22,tzinfo=timezone.utc))
  a=manufacture_receipt(p,c,"PARTIAL_ALIVE"); b=manufacture_receipt(p,c,"PARTIAL_ALIVE")
  self.assertEqual(a,b); self.assertFalse(a["body"]["actuation_performed"])
