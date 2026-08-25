import unittest
from dataclasses import replace
from scripts.release_train.distributional_robustness_crown.api import *
from scripts.release_train.distributional_robustness_crown.refusal import Refused
class T(unittest.TestCase):
 def test_brce_and_replay(self):
  with self.assertRaises(Refused): admit(Action.DO)
  self.assertTrue(admit(Action.DO,"BRCE")); r=Receipt.issue("s","PARTIAL_ALIVE","e"); self.assertEqual(replay(r),"REPLAY_MATCH")
  with self.assertRaises(Refused): replay(replace(r,standing="ALIVE"))
