import unittest
from datetime import datetime, timezone
from fractions import Fraction
from scripts.measure_train.detector_msa.subject import Subject, Refused
from scripts.measure_train.detector_msa.policy import DetectorPolicy
from scripts.measure_train.detector_msa.calibration import DetectorCalibration
from scripts.measure_train.detector_msa.admission import admit_current_detector

class DetectorAdmissionCourt(unittest.TestCase):
    def test_unreliable_detector_refuses_current_admission(self):
        subject = Subject("o/r", "a" * 40)
        policy = DetectorPolicy("det", "WINDOW_L1", 1, ())
        calibration = DetectorCalibration(policy.fingerprint, 1, 4, Fraction(1, 2), Fraction(0), Fraction(1), "UNRELIABLE")
        now = datetime.now(timezone.utc)
        with self.assertRaises(Refused):
            admit_current_detector(subject, policy, calibration, ((policy, calibration),), subject, now, now)
