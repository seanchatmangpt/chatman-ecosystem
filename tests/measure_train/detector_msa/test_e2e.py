import unittest
from fractions import Fraction
from scripts.measure_train.detector_msa.subject import Subject
from scripts.measure_train.detector_msa.policy import DetectorPolicy
from scripts.measure_train.detector_msa.calibration import DetectorCalibration
from scripts.measure_train.detector_msa.consensus import DetectorVote
from scripts.measure_train.detector_msa.qualify import qualify
from scripts.measure_train.detector_msa.receipt import replay

class DetectorMsaChicagoCourt(unittest.TestCase):
    def test_calibrated_independent_stability_then_disagreement(self):
        subject = Subject("o/r", "a" * 40)
        l1 = DetectorPolicy("l1", "WINDOW_L1", 1, ())
        cusum = DetectorPolicy("cusum", "PREQUENTIAL_CUSUM", 1, ())
        c1 = DetectorCalibration(l1.fingerprint, 1, 8, Fraction(0), Fraction(0), Fraction(2), "CALIBRATED")
        c2 = DetectorCalibration(cusum.fingerprint, 1, 8, Fraction(0), Fraction(0), Fraction(3), "CALIBRATED")
        first = DetectorVote("l1", "1" * 64, "STABLE", "e1")
        second = DetectorVote("cusum", "2" * 64, "STABLE", "e2")
        pair = frozenset((first.source_fingerprint, second.source_fingerprint))
        qualified = qualify(subject, ((l1, c1), (cusum, c2)), (first, second), frozenset((pair,)))
        self.assertEqual(qualified["standing"], "PARTIAL_ALIVE")
        self.assertEqual(replay(qualified["receipt"]), "REPLAY_MATCH")
        self.assertFalse(qualified["actuation_performed"])
        moved = DetectorVote("cusum", "2" * 64, "DRIFT", "e3")
        divergent = qualify(subject, ((l1, c1), (cusum, c2)), (first, moved), frozenset((pair,)))
        self.assertEqual(divergent["consensus"]["state"], "DIVERGED")
        self.assertEqual(divergent["standing"], "UNKNOWN")
