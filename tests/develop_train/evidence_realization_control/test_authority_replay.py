import unittest
from dataclasses import replace
from scripts.develop_train.evidence_realization_control import *
class T(unittest.TestCase):
 def test_do_refuses(self):
  with self.assertRaises(Refused): admit(ActionClass.DO)
 def test_replay(self):
  r=Receipt('o/r@'+'c'*40,1,'PARTIAL_ALIVE',('e',),'P'); self.assertEqual(replay(r,r.digest()),'REPLAY_MATCH')
  with self.assertRaises(Refused): replay(replace(r,actuation_performed=True),r.digest())
