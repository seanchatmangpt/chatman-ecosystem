import unittest
from datetime import datetime, timezone
from fractions import Fraction
from scripts.measure_train.federation_convergence_kinetics_msa.subject import Subject
from scripts.measure_train.federation_convergence_kinetics_msa.observation import Observation
from scripts.measure_train.federation_convergence_kinetics_msa.calibration import calibrate
from scripts.measure_train.federation_convergence_kinetics_msa.drift import Cusum

class TestCalibrationDrift(unittest.TestCase):
    def test_calibration_and_drift_are_distinct(self):
        subject = Subject("o/r", "a"*40, "b"*64, 1)
        now = datetime.now(timezone.utc)
        rows = [Observation(subject, str(i), 0, "ACTIVE", Fraction(9,10), str(i), "DISCOVERY", "E", "R", str(i), now) for i in range(10)]
        self.assertEqual(calibrate(rows, {str(i): True for i in range(10)}).state, "CALIBRATED")
        self.assertTrue(Cusum(reference=Fraction(1,10), threshold=Fraction(1,2)).run([Fraction(1,2)]*3)["drifted"])
