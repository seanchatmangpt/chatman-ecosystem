from fractions import Fraction
import unittest

from scripts.develop_train.calibrated_recovery_quorum.calibration_model import CalibrationModel
from scripts.develop_train.calibrated_recovery_quorum.likelihood import contribution
from scripts.develop_train.calibrated_recovery_quorum.sequential import decide


class TestLikelihoodSequential(unittest.TestCase):
    def test_pass_positive_and_pending_zero(self):
        model = CalibrationModel(
            "a" * 64,
            10,
            Fraction(9, 10),
            Fraction(1, 10),
            Fraction(0),
            Fraction(1, 2),
        )
        self.assertGreater(contribution(model, "PASS").value, 0)
        self.assertEqual(contribution(model, "PENDING").value, 0)
        self.assertEqual(decide((contribution(model, "PASS"),)).decision, "ACCEPT_BOUNDED")

    def test_fail_negative(self):
        model = CalibrationModel(
            "a" * 64,
            10,
            Fraction(9, 10),
            Fraction(1, 10),
            Fraction(0),
            Fraction(1, 2),
        )
        self.assertLess(contribution(model, "FAIL").value, 0)
