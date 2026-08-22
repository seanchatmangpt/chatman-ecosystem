import unittest
from fractions import Fraction
from scripts.measure_train.detector_msa.metrics import DetectorMetrics
from scripts.measure_train.detector_msa.calibration import calibrate

class DetectorCalibrationCourt(unittest.TestCase):
    def test_support_floor_and_quality_ceiling(self):
        sparse = DetectorMetrics("a" * 64, 3, 2, 1, 0, 0, 2, Fraction(0), Fraction(0), Fraction(1))
        self.assertEqual(calibrate(sparse, 1).state, "INSUFFICIENT")
        reliable = DetectorMetrics("a" * 64, 4, 2, 2, 0, 0, 2, Fraction(0), Fraction(0), Fraction(1))
        self.assertEqual(calibrate(reliable, 1).state, "CALIBRATED")
        noisy = DetectorMetrics("a" * 64, 4, 2, 2, 1, 0, 2, Fraction(1, 2), Fraction(0), Fraction(1))
        self.assertEqual(calibrate(noisy, 1).state, "UNRELIABLE")
