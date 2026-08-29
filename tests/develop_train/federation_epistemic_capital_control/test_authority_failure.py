from scripts.develop_train.federation_epistemic_capital_control import *
SUB=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40)
import unittest
class T(unittest.TestCase):
 def test_authority_replay(self):
  self.assertEqual(len(require_complete(list(FailureWorld))),7)
  with self.assertRaises(Refused): admit(Action.DO)
  self.assertEqual(admit(Action.DO,'BRCE'),Action.DO)
  r=Receipt(SUB.key,9,'PARTIAL_ALIVE','c'*64,'3')
  self.assertEqual(replay(r,r.digest),'REPLAY_MATCH')
  with self.assertRaises(Refused): replay(r,'0'*64)
