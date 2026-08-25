import unittest
from scripts.develop_train.sequential_acquisition.authority import ActionClass, admit_action
from scripts.develop_train.sequential_acquisition.failure_world import world
from scripts.develop_train.sequential_acquisition.receipt import Receipt, replay
from scripts.develop_train.sequential_acquisition.refusals import Refused

class ReceiptAuthorityFailureCourt(unittest.TestCase):
    def test_replay_seed_and_do_refusal(self):
        r=Receipt("seanchatmangpt/chatman-ecosystem@"+"b"*40,1,2,"c","UNKNOWN")
        self.assertTrue(replay(r,r.digest()))
        self.assertEqual(world("seed",["a","b","c"]),world("seed",["c","b","a"]))
        with self.assertRaises(Refused): admit_action(ActionClass.DO)
