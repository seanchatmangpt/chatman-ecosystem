import unittest
from scripts.develop_train.process_evidence_correspondence import *

class TestReplayAuthority(unittest.TestCase):
    def test_replay_and_authority(self):
        root=replay_root([ReplayNode("semantic","1"*64),ReplayNode("runtime","2"*64,("semantic",))])
        receipt=Receipt("o/r@"+"a"*40+"#"+"b"*64,1,"CONSERVATIVE","PARTIAL_ALIVE",root)
        self.assertEqual(replay(receipt,receipt.digest()),"REPLAY_MATCH")
        with self.assertRaises(Refused):
            replay(receipt,"0"*64)
        with self.assertRaises(Refused):
            admit(ActionClass.DO)
        self.assertTrue(admit(ActionClass.DO,"BRCE"))

if __name__ == "__main__": unittest.main()
