import unittest
from datetime import datetime, timezone
from fractions import Fraction

from scripts.release_train.evidence_acquisition.calibration import SensorCalibration
from scripts.release_train.evidence_acquisition.frontier import CalibrationFrontier

class FrontierMovementCourt(unittest.TestCase):
    def test_generation_movement_invalidates_plan(self):
        now = datetime.now(timezone.utc)
        before = (
            SensorCalibration("runtime", 7, 20, Fraction(9, 10), Fraction(1, 10), now),
            SensorCalibration("workflow", 4, 20, Fraction(4, 5), Fraction(1, 5), now),
        )
        after = (
            SensorCalibration("runtime", 8, 20, Fraction(9, 10), Fraction(1, 10), now),
            before[1],
        )
        frontier = CalibrationFrontier.build(before)
        frontier.assert_current(before)
        with self.assertRaisesRegex(ValueError, "STALE_CALIBRATION_FRONTIER"):
            frontier.assert_current(after)

if __name__ == "__main__":
    unittest.main()
