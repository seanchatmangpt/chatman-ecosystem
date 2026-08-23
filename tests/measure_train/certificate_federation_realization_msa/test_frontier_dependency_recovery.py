import unittest
from scripts.measure_train.certificate_federation_realization_msa.currentness import FederationModel, current
from scripts.measure_train.certificate_federation_realization_msa.dependency import graph
from scripts.measure_train.certificate_federation_realization_msa.recovery import classify
from scripts.measure_train.certificate_federation_realization_msa.subject import Refused

class TestFrontierDependencyRecovery(unittest.TestCase):
    def test_split_cycle_and_recovery(self):
        with self.assertRaises(Refused):
            current([FederationModel(2, "a"*64, "CALIBRATED"), FederationModel(2, "b"*64, "CALIBRATED")])
        with self.assertRaises(Refused):
            graph(["a", "b"], [("a", "b"), ("b", "a")])
        self.assertEqual(classify("CENSORED", "EXACT"), "OBSERVABILITY_RECOVERED")
        self.assertEqual(classify("DIVERGED", "EXACT"), "SEMANTIC_REPAIR")
