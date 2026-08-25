import unittest
from scripts.develop_train.outcome_transport_invariance import *

class CorrespondenceFailure(unittest.TestCase):
    def test_global_correspondence_and_failure_census(self):
        witnesses = [Engine("BEAM", "i1", "m1", "s", "t", "o"), Engine("WASM", "i2", "m2", "s", "t", "o")]
        self.assertTrue(engines(witnesses))
        regions_seen = [Region("h1", "us", "cert1", True, True), Region("h2", "eu", "cert2", True, True)]
        self.assertTrue(regions(regions_seen))
        self.assertEqual(len(require_failures(list(World))), 7)

    def test_engine_divergence_refuses(self):
        with self.assertRaises(Refused):
            engines([Engine("A", "i1", "m1", "s", "t", "o"), Engine("B", "i2", "m2", "s", "x", "o")])
