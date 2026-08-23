import unittest
from scripts.develop_train.process_intelligence_substrate import ActionClass, Receipt, admit_action, replay
from scripts.develop_train.process_intelligence_substrate.errors import Refused

class AuthorityReceiptTest(unittest.TestCase):
    def test_brce_and_replay(self):
        admit_action(ActionClass.CONSTRUCT)
        with self.assertRaises(Refused):
            admit_action(ActionClass.DO)
        receipt = Receipt("seanchatmangpt/chatman-ecosystem@" + "a"*40, "b"*64, "PARTIAL_ALIVE", ("SEMANTIC","REPLAY"))
        digest = receipt.digest()
        self.assertTrue(replay(receipt, digest))
        self.assertFalse(replay(receipt, "0"*64))
        with self.assertRaises(Refused):
            Receipt(receipt.subject, receipt.semantic_digest, receipt.standing, receipt.rails, True).digest()

if __name__ == "__main__": unittest.main()
