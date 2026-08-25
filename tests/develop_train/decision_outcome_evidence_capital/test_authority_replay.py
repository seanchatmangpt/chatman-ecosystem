import unittest
from scripts.develop_train.decision_outcome_evidence_capital import *

class AuthorityReplay(unittest.TestCase):
    def test_brce_and_replay(self):
        with self.assertRaises(Refused):
            admit(ActionClass.DO)
        self.assertEqual(admit(ActionClass.DO,"BRCE"),ActionClass.DO)
        subject=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40)
        r=Receipt(subject.key,3,"PARTIAL_ALIVE","e"*64)
        self.assertEqual(replay(r,r.digest),"REPLAY_MATCH")
        with self.assertRaises(Refused):
            replay(r,"0"*64)

    def test_reported_actuation_refuses(self):
        with self.assertRaises(Refused):
            Receipt("seanchatmangpt/chatman-ecosystem@"+"a"*40,3,"UNKNOWN","e"*64,actuation_performed=True)

if __name__=="__main__": unittest.main()
