import unittest
from dataclasses import replace
from scripts.release_train.promotion_epoch.receipt import manufacture,replay
class T(unittest.TestCase):
 def test_replay(self):
  r=manufacture("a"*40,"b"*40,("x",),"ALIVE"); self.assertTrue(replay(r))
 def test_tamper(self):
  r=manufacture("a"*40,"b"*40,("x",),"ALIVE"); self.assertFalse(replay(replace(r,selected=("y",))))
