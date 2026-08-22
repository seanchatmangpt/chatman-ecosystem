import unittest
from scripts.release_train.promotion_intent_lease.receipt import Receipt
class T(unittest.TestCase):
 def test_replay_and_tamper(self):
  r=Receipt.manufacture({'x':1}); self.assertTrue(r.replay())
  bad=Receipt({**r.payload,'x':2},r.digest); self.assertFalse(bad.replay())
