import unittest
from datetime import datetime,timezone
from scripts.measure_train.consistent_cut.subject import Subject
from scripts.measure_train.consistent_cut.epoch import EpochStamp
from scripts.measure_train.consistent_cut.cut import ConsistentCut
from scripts.measure_train.consistent_cut.receipt import manufacture_receipt
class T(unittest.TestCase):
 def test_deterministic_no_do(self):
  now=datetime(2026,8,22,tzinfo=timezone.utc); e=EpochStamp(Subject("p/r","a"*40),1,"1"*64,now); cut=ConsistentCut((e,))
  a=manufacture_receipt(Subject("c/r","b"*40),cut,(("p/r","REPOSITORY","PASS"),),"PARTIAL_ALIVE")
  b=manufacture_receipt(Subject("c/r","b"*40),cut,(("p/r","REPOSITORY","PASS"),),"PARTIAL_ALIVE")
  self.assertEqual(a,b); self.assertFalse(a["body"]["actuation_performed"])
