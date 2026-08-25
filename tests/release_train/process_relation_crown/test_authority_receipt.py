import unittest
from scripts.release_train.process_relation_crown.authority import ActionClass,admit
from scripts.release_train.process_relation_crown.receipt import Receipt,replay
from scripts.release_train.process_relation_crown.refusal import Refused
class T(unittest.TestCase):
 def test_brce_and_replay(self):
  with self.assertRaises(Refused): admit(ActionClass.DO)
  admit(ActionClass.DO,"BRCE")
  r=Receipt("o/r@"+"a"*40,"EXACT","b"*64,"STRONGEST_DEFENSIBLE","PARTIAL_ALIVE")
  self.assertEqual(replay(r,r.digest),"REPLAY_MATCH")
  with self.assertRaises(Refused): replay(r,"0"*64)
