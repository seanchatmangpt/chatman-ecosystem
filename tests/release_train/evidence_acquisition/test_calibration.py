import unittest
from datetime import datetime, timedelta, timezone
from fractions import Fraction

from scripts.release_train.evidence_acquisition.calibration import SensorCalibration

class CalibrationCourt(unittest.TestCase):
    def test_support_and_freshness(self):
        now = datetime(2026, 8, 22, 22, 0, tzinfo=timezone.utc)
        good = SensorCalibration("a", 1, 20, Fraction(9, 10), Fraction(1, 10), now - timedelta(minutes=5))
        good.admit(now)
        weak = SensorCalibration("a", 1, 2, Fraction(9, 10), Fraction(1, 10), now)
        with self.assertRaisesRegex(ValueError, "INSUFFICIENT_CALIBRATION_SUPPORT"):
            weak.admit(now)
        stale = SensorCalibration("a", 1, 20, Fraction(9, 10), Fraction(1, 10), now - timedelta(hours=3))
        with self.assertRaisesRegex(ValueError, "STALE_CALIBRATION"):
            stale.admit(now)

if __name__ == "__main__":
    unittest.main()
