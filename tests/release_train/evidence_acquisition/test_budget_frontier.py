import unittest
from datetime import datetime, timezone
from fractions import Fraction

from scripts.release_train.evidence_acquisition.budget import AcquisitionBudget
from scripts.release_train.evidence_acquisition.calibration import SensorCalibration
from scripts.release_train.evidence_acquisition.candidate import EvidenceCandidate
from scripts.release_train.evidence_acquisition.frontier import CalibrationFrontier

class BudgetFrontierCourt(unittest.TestCase):
    def test_budget_and_stale_frontier(self):
        candidate = EvidenceCandidate("a", "cusum", "runtime", "repo", 10, 5)
        with self.assertRaisesRegex(ValueError, "ACQUISITION_COST_BUDGET"):
            AcquisitionBudget(5, 10, 1).admit((candidate,))
        now = datetime.now(timezone.utc)
        old = SensorCalibration("a", 1, 20, Fraction(9, 10), Fraction(1, 10), now)
        moved = SensorCalibration("a", 2, 20, Fraction(9, 10), Fraction(1, 10), now)
        frontier = CalibrationFrontier.build((old,))
        with self.assertRaisesRegex(ValueError, "STALE_CALIBRATION_FRONTIER"):
            frontier.assert_current((moved,))

if __name__ == "__main__":
    unittest.main()
