import unittest
from scripts.measure_train.detector_msa.consensus import DetectorVote, consensus
from scripts.measure_train.detector_msa.standing import bounded_standing

class DetectorConsensusStandingCourt(unittest.TestCase):
    def test_independent_stability_is_bounded_and_failure_dominates(self):
        first = DetectorVote("a", "1" * 64, "STABLE", "e1")
        second = DetectorVote("b", "2" * 64, "STABLE", "e2")
        pair = frozenset((first.source_fingerprint, second.source_fingerprint))
        result = consensus((first, second), frozenset((pair,)))
        self.assertEqual(result["state"], "STABLE_CONFIRMED")
        self.assertEqual(bounded_standing(result), "PARTIAL_ALIVE")
        self.assertEqual(bounded_standing(result, ("FAIL",)), "BUILD_BROKEN")
