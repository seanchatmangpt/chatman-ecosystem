import unittest
from scripts.measure_train.detector_msa.subject import Subject, Refused
from scripts.measure_train.detector_msa.receipt import manufacture_receipt, replay

class DetectorReceiptCourt(unittest.TestCase):
    def test_receipt_tamper_and_actuation_fail_closed(self):
        receipt = manufacture_receipt(Subject("o/r", "a" * 40), (), {"state": "INSUFFICIENT", "independent_count": 0}, "UNKNOWN")
        self.assertEqual(replay(receipt), "REPLAY_MATCH")
        self.assertFalse(receipt["body"]["actuation_performed"])
        receipt["body"]["standing"] = "PARTIAL_ALIVE"
        with self.assertRaises(Refused):
            replay(receipt)
