import unittest
from scripts.develop_train.distributional_process_capital.errors import Refused
from scripts.develop_train.distributional_process_capital.authority import Action,admit
from scripts.develop_train.distributional_process_capital.receipt import Receipt,replay
class AuthorityReplayCourt(unittest.TestCase):
    def test_brce_and_replay(self):
        with self.assertRaises(Refused): admit(Action.DO)
        self.assertEqual(admit(Action.DO,"BRCE"),Action.DO)
        receipt=Receipt("seanchatmangpt/chatman-ecosystem@"+"a"*40+"#"+"b"*64,"MIN_WORST","PARTIAL_ALIVE","e"*64)
        self.assertEqual(replay(receipt,receipt.digest),"REPLAY_MATCH")
        with self.assertRaises(Refused): replay(receipt,"0"*64)
if __name__=="__main__": unittest.main()
