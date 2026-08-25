import unittest
from fractions import Fraction
from scripts.measure_train.certificate_federation_realization_msa.quorum import QuorumRealization
from scripts.measure_train.certificate_federation_realization_msa.calibration import calibrate

class TestQuorumCalibration(unittest.TestCase):
    def test_false_current_is_directional(self):
        rows = [QuorumRealization(2, True, False, 1)] + [QuorumRealization(2, True, True, 2) for _ in range(9)]
        calibration = calibrate(rows, min_support=5, max_false_current=Fraction(1, 10))
        self.assertEqual(calibration.state, "CALIBRATED")
        self.assertEqual(calibration.false_current_rate, Fraction(1, 10))
