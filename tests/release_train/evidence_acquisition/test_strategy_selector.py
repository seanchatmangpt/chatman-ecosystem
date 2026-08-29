import unittest
from datetime import datetime, timezone
from fractions import Fraction

from scripts.release_train.evidence_acquisition.belief import Belief
from scripts.release_train.evidence_acquisition.budget import AcquisitionBudget
from scripts.release_train.evidence_acquisition.calibration import SensorCalibration
from scripts.release_train.evidence_acquisition.candidate import EvidenceCandidate
from scripts.release_train.evidence_acquisition.independence import IndependenceProof
from scripts.release_train.evidence_acquisition.selector import select
from scripts.release_train.evidence_acquisition.strategy import Strategy

class StrategySelectorCourt(unittest.TestCase):
    def test_strategy_selection_is_dependency_bounded(self):
        now = datetime.now(timezone.utc)
        candidates = (
            EvidenceCandidate("a", "cusum", "runtime", "repo", 10, 5),
            EvidenceCandidate("b", "ewma", "workflow", "repo", 20, 7),
        )
        calibrations = (
            SensorCalibration("a", 1, 20, Fraction(9, 10), Fraction(1, 10), now),
            SensorCalibration("b", 1, 20, Fraction(4, 5), Fraction(1, 5), now),
        )
        proofs = (IndependenceProof("a", "b"),)
        budget = AcquisitionBudget(100, 100, 2)
        belief = Belief(Fraction(1, 4), 1)
        for strategy in (Strategy.MAX_INFORMATION_GAIN, Strategy.MAX_INFORMATION_PER_COST):
            selected = select(belief, candidates, calibrations, proofs, budget, strategy)
            self.assertEqual({item.id for item in selected}, {"a", "b"})

if __name__ == "__main__":
    unittest.main()
