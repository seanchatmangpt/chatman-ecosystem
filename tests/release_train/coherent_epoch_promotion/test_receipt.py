import unittest
from dataclasses import replace
from scripts.release_train.coherent_epoch_promotion.receipt import manufacture,replay
class T(unittest.TestCase):
 def test_tamper_refuses(self):
  r=manufacture({'x':1}); self.assertTrue(replay(r)); self.assertFalse(replay(replace(r,payload={'x':2})))
