import unittest
from scripts.measure_train.compatibility.subject_vector import Subject
from scripts.measure_train.compatibility.receipt import make_receipt
from scripts.measure_train.compatibility.replay import replay
class T(unittest.TestCase):
 def test_tamper(self):
  r=make_receipt(Subject("a/b","a"*40),"PARTIAL_ALIVE",["focused:PASS"]); r["digest"]="0"*64; self.assertEqual(replay(r),"REFUSED[RECEIPT_MISMATCH]")
