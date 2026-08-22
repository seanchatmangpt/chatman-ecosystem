import unittest
from dataclasses import replace
from scripts.develop_train.recovery_transaction.receipt import QualificationReceipt, replay

class T(unittest.TestCase):
    def test_receipt_replays_and_tamper_fails(self):
        receipt = QualificationReceipt("consumer", "a" * 64, "b" * 64, "CAS_RESELECT", "REQUALIFYING", (), "MEMORY")
        digest = receipt.digest
        self.assertTrue(replay(receipt, digest))
        self.assertFalse(replay(replace(receipt, standing="BLOCKED"), digest))
        actuated = replace(receipt, actuation_performed=True)
        self.assertFalse(replay(actuated, actuated.digest))

if __name__ == "__main__":
    unittest.main()
