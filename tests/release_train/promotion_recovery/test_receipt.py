import unittest
from scripts.release_train.promotion_recovery.receipt import manufacture,replay
from scripts.release_train.promotion_recovery.subject import Refusal
class T(unittest.TestCase):
 def test_tamper_refuses(self):
  r=manufacture({'x':1}); self.assertTrue(replay(r)); r['payload']['x']=2
  with self.assertRaisesRegex(Refusal,'RECEIPT_MISMATCH'): replay(r)
