import unittest
from scripts.develop_train.certificate_federation_realization_control import *
SUB=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40)
class AuthorityReceipt(unittest.TestCase):
    def test_brce_and_receipt(self):
        with self.assertRaises(Refused): admit(Action.DO)
        self.assertEqual(admit(Action.DO,"BRCE"),Action.DO)
        receipt=Receipt(SUB.key,7,"PARTIAL_ALIVE","d"*64)
        self.assertEqual(replay(receipt,receipt.digest),"REPLAY_MATCH")
        with self.assertRaises(Refused): replay(receipt,"0"*64)
if __name__=="__main__": unittest.main()
