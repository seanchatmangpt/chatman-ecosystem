import unittest
from scripts.measure_train.provenance.subject import Subject,Refused
from scripts.measure_train.provenance.receipt import manufacture_receipt
from scripts.measure_train.provenance.replay import replay
class T(unittest.TestCase):
 def test_tamper(self):
  r=manufacture_receipt(Subject("o/r","a"*40),{"standing":"UNKNOWN"},(),None); self.assertEqual(replay(r),"REPLAY_MATCH")
  r["body"]["sha"]="b"*40
  with self.assertRaises(Refused): replay(r)
