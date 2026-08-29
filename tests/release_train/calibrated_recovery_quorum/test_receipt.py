import unittest
from scripts.release_train.calibrated_recovery_quorum.receipt import Receipt
class T(unittest.TestCase):
 def test_replay_and_tamper(self):
  r=Receipt.manufacture({"x":1}); self.assertTrue(r.replay())
  with self.assertRaises(Exception): Receipt({**r.payload,"x":2},r.digest).replay()
