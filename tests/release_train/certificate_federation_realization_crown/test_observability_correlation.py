import unittest
from scripts.release_train.certificate_federation_realization_crown import *
from scripts.release_train.certificate_federation_realization_crown.refusal import Refused
class TestObservabilityCorrelation(unittest.TestCase):
    def test_wilson_and_independence(self):
        self.assertGreater(wilson_lower(8,10),0.4)
        self.assertLess(abs(require_independent([1,1,0,0,1,0,1,0],[1,0,1,0,0,1,0,1],0.9)),0.9)
    def test_perfect_correlation_refuses(self):
        with self.assertRaises(Refused): require_independent([1,1,0,0],[1,1,0,0],0.5)
