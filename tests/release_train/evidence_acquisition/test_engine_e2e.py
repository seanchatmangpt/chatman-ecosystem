import unittest
from datetime import datetime, timezone
from fractions import Fraction

from scripts.release_train.evidence_acquisition.belief import Belief
from scripts.release_train.evidence_acquisition.budget import AcquisitionBudget
from scripts.release_train.evidence_acquisition.calibration import SensorCalibration
from scripts.release_train.evidence_acquisition.candidate import EvidenceCandidate
from scripts.release_train.evidence_acquisition.dependency import DependencyGraph
from scripts.release_train.evidence_acquisition.engine import qualify
from scripts.release_train.evidence_acquisition.frontier import CalibrationFrontier
from scripts.release_train.evidence_acquisition.independence import IndependenceProof
from scripts.release_train.evidence_acquisition.strategy import Strategy

class EngineE2ECourt(unittest.TestCase):
    def test_requalifying_and_dependency_blocked_paths(self):
        now = datetime.now(timezone.utc)
        subject = "seanchatmangpt/chatman-ecosystem@" + "a" * 40
        candidates = (
            EvidenceCandidate("runtime", "cusum", "runtime", "repo", 10, 5),
            EvidenceCandidate("workflow", "ewma", "workflow", "repo", 10, 5),
        )
        calibrations = (
            SensorCalibration("runtime", 3, 20, Fraction(9, 10), Fraction(1, 10), now),
            SensorCalibration("workflow", 4, 20, Fraction(4, 5), Fraction(1, 5), now),
        )
        frontier = CalibrationFrontier.build(calibrations)
        graph = DependencyGraph((("seanchatmangpt/chatman-ecosystem", "seanchatmangpt/gymact"),))
        common = dict(subject_value=subject, belief=Belief(Fraction(1, 4), 1), candidates=candidates, calibrations=calibrations,
                      proofs=(IndependenceProof("runtime", "workflow"),), budget=AcquisitionBudget(100, 100, 2),
                      strategy=Strategy.MAX_INFORMATION_GAIN, frontier=frontier, dependencies=graph, now=now)
        healthy = qualify(dependency_standing={"seanchatmangpt/gymact": "PARTIAL_ALIVE"}, **common)
        self.assertEqual(healthy.standing, "REQUALIFYING")
        self.assertEqual(healthy.phases, ("VERIFY", "CONSTRUCT"))
        self.assertTrue(healthy.receipt.replay(healthy.receipt.digest()))
        self.assertFalse(healthy.receipt.actuation_performed)
        blocked = qualify(dependency_standing={"seanchatmangpt/gymact": "BUILD_BROKEN"}, **common)
        self.assertEqual(blocked.standing, "BLOCKED")
        self.assertEqual(blocked.selected_ids, ())

if __name__ == "__main__":
    unittest.main()
