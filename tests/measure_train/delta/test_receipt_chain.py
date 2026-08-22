import unittest
from scripts.measure_train.delta.receipt_chain import manufacture,replay
class T(unittest.TestCase):
 def test_replay_tamper_refuses(self):
  b,d=manufacture({'x':1},'a'*64); self.assertTrue(replay(b,d)); b['payload']['x']=2; self.assertFalse(replay(b,d))
