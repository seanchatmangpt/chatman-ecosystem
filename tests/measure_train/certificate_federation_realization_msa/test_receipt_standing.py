import unittest
from fractions import Fraction
from scripts.measure_train.certificate_federation_realization_msa.subject import Subject, Refused
from scripts.measure_train.certificate_federation_realization_msa.certificate import Certificate
from scripts.measure_train.certificate_federation_realization_msa.calibration import Calibration
from scripts.measure_train.certificate_federation_realization_msa.standing import standing
from scripts.measure_train.certificate_federation_realization_msa.receipt import manufacture
from scripts.measure_train.certificate_federation_realization_msa.replay import replay

class TestReceiptStanding(unittest.TestCase):
    def test_failure_dominance_and_tamper(self):
        calibration = Calibration(10, Fraction(0), Fraction(0), "CALIBRATED")
        self.assertEqual(standing(calibration, ["BUILD_BROKEN"]), "BUILD_BROKEN")
        receipt = manufacture(Certificate(Subject("o/r", "a"*40, "b"*64), 1, "c"*64), calibration, "PARTIAL_ALIVE")
        self.assertEqual(replay(receipt), "REPLAY_MATCH")
        receipt["body"]["standing"] = "ALIVE"
        with self.assertRaises(Refused):
            replay(receipt)
