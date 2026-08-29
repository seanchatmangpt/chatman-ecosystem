import unittest
from scripts.release_train.replicated_policy_admission.receipt import Receipt,replay
from scripts.release_train.replicated_policy_admission.refusal import Refused
class TestReceipt(unittest.TestCase):
    def test_replay_and_tamper(self):
        r=Receipt('a/b@'+'0'*40,1,'a'*64,'b'*64,('r1','r2'),(),'PARTIAL_ALIVE','OK'); self.assertTrue(replay(r,r.digest)); self.assertFalse(replay(r,'0'*64))
    def test_reported_actuation_refuses(self):
        r=Receipt('a/b@'+'0'*40,1,None,None,(),(),'UNKNOWN','X',actuation_performed=True)
        with self.assertRaises(Refused): replay(r,r.digest)
