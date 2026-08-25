import unittest
from scripts.release_train.calibrated_composition_crown import *
class T(unittest.TestCase):
 def test_do_and_replay(self):
  with self.assertRaises(Refused): admit_action(ActionClass.DO)
  r=Receipt("s",1,"MAX_COVERAGE","CONSERVATIVE","PARTIAL_ALIVE",())
  self.assertEqual(replay(r,r.digest()),"REPLAY_MATCH")
  with self.assertRaises(Refused): replay(r,"0"*64)
