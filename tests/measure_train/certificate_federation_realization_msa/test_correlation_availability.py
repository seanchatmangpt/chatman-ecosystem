import unittest
from scripts.measure_train.certificate_federation_realization_msa.correlation import phi_failure
from scripts.measure_train.certificate_federation_realization_msa.availability import wilson

class TestCorrelationAvailability(unittest.TestCase):
    def test_failure_correlation_and_wilson_bounds(self):
        self.assertGreater(phi_failure([1,1,0,0], [1,1,0,0]), 0.9)
        low, high = wilson(8, 10)
        self.assertLess(low, 0.8)
        self.assertGreater(high, 0.8)
