from datetime import datetime, timezone
import unittest

from scripts.develop_train.calibrated_recovery_quorum.calibration_trial import CalibrationTrial
from scripts.develop_train.calibrated_recovery_quorum.subject import Subject


class TestSubjectTrial(unittest.TestCase):
    def test_exact_identity_and_trial_digest(self):
        subject = Subject("a/b", "a" * 40)
        self.assertEqual(subject.exact, "a/b@" + "a" * 40)
        trial = CalibrationTrial("src", True, "PASS", datetime.now(timezone.utc))
        self.assertEqual(len(trial.trial_id), 64)

    def test_inexact_and_naive_refuse(self):
        with self.assertRaisesRegex(ValueError, "INEXACT_SUBJECT_SHA"):
            Subject("a/b", "abc")
        with self.assertRaisesRegex(ValueError, "NAIVE_CALIBRATION_TIME"):
            CalibrationTrial("src", True, "PASS", datetime.now())
