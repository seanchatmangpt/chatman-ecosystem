import unittest
from scripts.measure_train.detector_msa.policy import DetectorPolicy

class DetectorPolicyCourt(unittest.TestCase):
    def test_parameter_order_cannot_change_identity(self):
        first = DetectorPolicy("det", "WINDOW_L1", 1, (("z", "2"), ("a", "1")))
        second = DetectorPolicy("det", "WINDOW_L1", 1, (("a", "1"), ("z", "2")))
        self.assertEqual(first.fingerprint, second.fingerprint)
