import unittest
from dataclasses import replace

from scripts.release_train.evidence_acquisition.authority import ActionClass, admit_action
from scripts.release_train.evidence_acquisition.receipt import QualificationReceipt

class AuthorityReceiptCourt(unittest.TestCase):
    def test_do_and_tamper_refusal(self):
        with self.assertRaisesRegex(ValueError, "BRCE_REQUIRED"):
            admit_action(ActionClass.DO)
        receipt = QualificationReceipt.issue("seanchatmangpt/chatman-ecosystem@" + "a" * 40, "f" * 64, "MAX_INFORMATION_GAIN", ("b", "a"), "REQUALIFYING")
        digest = receipt.digest()
        self.assertTrue(receipt.replay(digest))
        self.assertFalse(replace(receipt, standing="ALIVE").replay(digest))
        self.assertFalse(replace(receipt, actuation_performed=True).replay(digest))

if __name__ == "__main__":
    unittest.main()
