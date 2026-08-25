import unittest
from scripts.develop_train.process_transition_substrate import *
class T(unittest.TestCase):
 def test_receipt_replay(self):
  r=Receipt("seanchatmangpt/chatman-ecosystem@"+"2"*40,3,"PARTIAL_ALIVE","3"*64)
  self.assertEqual(replay(r,r.digest()),"REPLAY_MATCH")
  with self.assertRaises(Refused): replay(r,"0"*64)
 def test_do(self):
  with self.assertRaises(Refused): admit_action(ActionClass.DO)
  self.assertTrue(admit_action(ActionClass.DO,"BRCE","4"*64,True))
