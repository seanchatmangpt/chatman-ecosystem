import unittest
from scripts.measure_train.detector_msa.independence import DetectorSource, relation

class DetectorIndependenceCourt(unittest.TestCase):
    def test_shared_runtime_cannot_be_laundered_as_independent(self):
        first = DetectorSource("a", "family-a", "impl-a", "runtime-shared")
        second = DetectorSource("b", "family-b", "impl-b", "runtime-shared")
        pair = frozenset((first.fingerprint, second.fingerprint))
        self.assertEqual(relation(first, second, frozenset((pair,))), "CORRELATED")
