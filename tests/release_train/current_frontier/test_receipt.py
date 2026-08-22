import unittest
from scripts.release_train.current_frontier.receipt import manufacture, replay, Receipt, Refusal
class T(unittest.TestCase):
 def test_replay(self): replay(manufacture({"x":1}))
 def test_tamper(self):
  r=manufacture({"x":1}); bad=Receipt(r.schema,{**r.body,"x":2},r.digest)
  with self.assertRaises(Refusal): replay(bad)
