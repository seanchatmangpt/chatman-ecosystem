import unittest
from scripts.measure_train.selection_provenance.strategy import StrategyBinding
from scripts.measure_train.selection_provenance.subject import Refused

class TestStrategy(unittest.TestCase):
    def test_strategy_fingerprint_binds_policy_and_parameters(self):
        a = StrategyBinding("LATEST_COMPLETE", "1"*64, (("k","v"),))
        b = StrategyBinding("LATEST_COMPLETE", "2"*64, (("k","v"),))
        self.assertNotEqual(a.fingerprint, b.fingerprint)
        with self.assertRaises(Refused):
            StrategyBinding("LATEST_COMPLETE", "1"*64, (("k","1"),("k","2")))
