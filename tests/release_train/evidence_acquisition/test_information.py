import unittest
from datetime import datetime, timezone
from fractions import Fraction

from scripts.release_train.evidence_acquisition.belief import Belief
from scripts.release_train.evidence_acquisition.calibration import SensorCalibration
from scripts.release_train.evidence_acquisition.information import expected_information_gain, posterior_defect

class InformationCourt(unittest.TestCase):
    def test_direction_and_gain(self):
        belief = Belief(Fraction(1, 4), 1)
        calibration = SensorCalibration("a", 1, 20, Fraction(9, 10), Fraction(1, 10), datetime.now(timezone.utc))
        self.assertLess(posterior_defect(belief, calibration, "PASS"), belief.defect)
        self.assertGreater(posterior_defect(belief, calibration, "FAIL"), belief.defect)
        self.assertGreater(expected_information_gain(belief, calibration), 0.0)

if __name__ == "__main__":
    unittest.main()
