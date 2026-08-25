import unittest
from fractions import Fraction
from scripts.measure_train.detector_msa.policy import DetectorPolicy
from scripts.measure_train.detector_msa.calibration import DetectorCalibration
from scripts.measure_train.detector_msa.frontier import current_calibration_frontier
from scripts.measure_train.detector_msa.subject import Refused

class DetectorFrontierCourt(unittest.TestCase):
    def test_divergent_same_generation_refuses(self):
        first = DetectorPolicy("det", "WINDOW_L1", 1, ())
        second = DetectorPolicy("det", "WINDOW_L1", 1, (("threshold", "2"),))
        c1 = DetectorCalibration(first.fingerprint, 1, 4, Fraction(0), Fraction(0), Fraction(1), "CALIBRATED")
        c2 = DetectorCalibration(second.fingerprint, 1, 4, Fraction(0), Fraction(0), Fraction(1), "CALIBRATED")
        with self.assertRaises(Refused):
            current_calibration_frontier((first, second), (c1, c2))
