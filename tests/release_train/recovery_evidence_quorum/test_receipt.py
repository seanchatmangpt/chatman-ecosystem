import unittest
from scripts.release_train.recovery_evidence_quorum.receipt import manufacture_receipt,replay
class T(unittest.TestCase):
 def test_replay(self): self.assertTrue(replay(manufacture_receipt({"x":1})))
 def test_tamper(self):
  r=manufacture_receipt({"x":1}); r["body"]["x"]=2; self.assertFalse(replay(r))
