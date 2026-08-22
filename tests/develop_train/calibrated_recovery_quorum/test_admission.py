from datetime import datetime, timedelta, timezone
from fractions import Fraction
import unittest

from scripts.develop_train.calibrated_recovery_quorum.admission import admit_witness
from scripts.develop_train.calibrated_recovery_quorum.calibration_model import CalibrationModel
from scripts.develop_train.calibrated_recovery_quorum.witness import RecoveryWitness


class TestAdmission(unittest.TestCase):
    def test_under_calibrated_and_future_refuse(self):
        now = datetime.now(timezone.utc)
        source = "a" * 64
        weak = CalibrationModel(
            source,
            2,
            Fraction(1, 2),
            Fraction(1, 2),
            Fraction(0),
            Fraction(0),
        )
        witness = RecoveryWitness("att", source, "PASS", now, "repo")
        self.assertEqual(
            admit_witness(
                witness,
                attempt_id="att",
                now=now,
                calibration=weak,
                min_trials=4,
            )[1],
            "REFUSED[UNDER_CALIBRATED_SOURCE]",
        )
        future = RecoveryWitness("att", source, "PASS", now + timedelta(seconds=1), "repo")
        strong = CalibrationModel(
            source,
            5,
            Fraction(3, 4),
            Fraction(1, 4),
            Fraction(0),
            Fraction(1, 2),
        )
        self.assertEqual(
            admit_witness(
                future,
                attempt_id="att",
                now=now,
                calibration=strong,
                min_trials=4,
            )[1],
            "REFUSED[FUTURE_EVIDENCE]",
        )
