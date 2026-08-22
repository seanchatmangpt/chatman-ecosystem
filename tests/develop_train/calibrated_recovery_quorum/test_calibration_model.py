from datetime import datetime, timedelta, timezone
from fractions import Fraction
import unittest

from scripts.develop_train.calibrated_recovery_quorum.calibration_model import fit_calibration
from scripts.develop_train.calibrated_recovery_quorum.calibration_trial import CalibrationTrial


class TestCalibration(unittest.TestCase):
    def test_smoothed_rates_and_support(self):
        now = datetime.now(timezone.utc)
        pairs = [(1, "PASS"), (1, "PASS"), (0, "FAIL"), (0, "PASS")]
        trials = tuple(
            CalibrationTrial("s", truth, predicted, now + timedelta(seconds=index))
            for index, (truth, predicted) in enumerate(pairs)
        )
        model = fit_calibration("s", trials, min_trials=4)
        self.assertEqual(model.support, 4)
        self.assertEqual(model.true_positive_rate, Fraction(3, 4))
        self.assertEqual(model.false_positive_rate, Fraction(2, 4))

    def test_duplicate_refuses(self):
        now = datetime.now(timezone.utc)
        trial = CalibrationTrial("s", True, "PASS", now)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CALIBRATION_TRIAL"):
            fit_calibration("s", (trial, trial))
